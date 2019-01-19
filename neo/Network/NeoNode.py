import binascii
import random
import datetime
from twisted.internet.protocol import Protocol
from twisted.internet import error as twisted_error
from twisted.internet import reactor, task, defer
from twisted.internet.address import IPv4Address
from twisted.internet.defer import CancelledError
from twisted.internet import error
from neo.Core.Blockchain import Blockchain as BC
from neocore.IO.BinaryReader import BinaryReader
from neo.Network.Message import Message
from neo.IO.MemoryStream import StreamManager
from neo.IO.Helper import Helper as IOHelper
from neo.Core.Helper import Helper
from .Payloads.GetBlocksPayload import GetBlocksPayload
from .Payloads.InvPayload import InvPayload
from .Payloads.NetworkAddressWithTime import NetworkAddressWithTime
from .Payloads.VersionPayload import VersionPayload
from .Payloads.HeadersPayload import HeadersPayload
from .Payloads.AddrPayload import AddrPayload
from .InventoryType import InventoryType
from neo.Settings import settings
from neo.logging import log_manager
from neo.Network.address import Address

logger = log_manager.getLogger('network')
logger_verbose = log_manager.getLogger('network.verbose')
MODE_MAINTAIN = 7
MODE_CATCHUP = 2

mode_to_name = {MODE_CATCHUP: 'CATCHUP', MODE_MAINTAIN: 'MAINTAIN'}

HEARTBEAT_BLOCKS = 'B'
HEARTBEAT_HEADERS = 'H'


class NeoNode(Protocol):
    Version = None

    leader = None

    identifier = None

    def has_tasks_running(self):
        block = False
        header = False
        peer = False
        if self.block_loop and self.block_loop.running:
            block = True

        if self.peer_loop and self.peer_loop.running:
            peer = True

        if self.header_loop and self.header_loop.running:
            header = True

        return block and header and peer

    def start_all_tasks(self):
        if not self.disconnecting:
            self.start_block_loop()
            self.start_header_loop()
            self.start_peerinfo_loop()

    def start_block_loop(self):
        logger_verbose.debug(f"{self.prefix} start_block_loop")
        if self.block_loop and self.block_loop.running:
            logger_verbose.debug(f"start_block_loop: still running -> stopping...")
            self.stop_block_loop()
        self.block_loop = task.LoopingCall(self.AskForMoreBlocks)
        self.block_loop_deferred = self.block_loop.start(self.sync_mode, now=False)
        self.block_loop_deferred.addErrback(self.OnLoopError)
        # self.leader.task_handles[self.block_loop] = self.prefix + f"{'block_loop':>15}"

    def stop_block_loop(self, cancel=True):
        logger_verbose.debug(f"{self.prefix} stop_block_loop: cancel -> {cancel}")
        if self.block_loop:
            logger_verbose.debug(f"{self.prefix} self.block_loop true")
            if self.block_loop.running:
                logger_verbose.debug(f"{self.prefix} stop_block_loop, calling stop")
                self.block_loop.stop()
        if cancel and self.block_loop_deferred:
            logger_verbose.debug(f"{self.prefix} stop_block_loop: trying to cancel")
            self.block_loop_deferred.cancel()

    def start_peerinfo_loop(self):
        logger_verbose.debug(f"{self.prefix} start_peerinfo_loop")
        if self.peer_loop and self.peer_loop.running:
            logger_verbose.debug(f"start_peer_loop: still running -> stopping...")
            self.stop_peerinfo_loop()
        self.peer_loop = task.LoopingCall(self.RequestPeerInfo)
        self.peer_loop_deferred = self.peer_loop.start(120, now=False)
        self.peer_loop_deferred.addErrback(self.OnLoopError)
        # self.leader.task_handles[self.peer_loop] = self.prefix + f"{'peerinfo_loop':>15}"

    def stop_peerinfo_loop(self, cancel=True):
        logger_verbose.debug(f"{self.prefix} stop_peerinfo_loop: cancel -> {cancel}")
        if self.peer_loop and self.peer_loop.running:
            logger_verbose.debug(f"{self.prefix} stop_peerinfo_loop, calling stop")
            self.peer_loop.stop()
        if cancel and self.peer_loop_deferred:
            logger_verbose.debug(f"{self.prefix} stop_peerinfo_loop: trying to cancel")
            self.peer_loop_deferred.cancel()

    def start_header_loop(self):
        logger_verbose.debug(f"{self.prefix} start_header_loop")
        if self.header_loop and self.header_loop.running:
            logger_verbose.debug(f"start_header_loop: still running -> stopping...")
            self.stop_header_loop()
        self.header_loop = task.LoopingCall(self.AskForMoreHeaders)
        self.header_loop_deferred = self.header_loop.start(5, now=False)
        self.header_loop_deferred.addErrback(self.OnLoopError)
        # self.leader.task_handles[self.header_loop] = self.prefix + f"{'header_loop':>15}"

    def stop_header_loop(self, cancel=True):
        logger_verbose.debug(f"{self.prefix} stop_header_loop: cancel -> {cancel}")
        if self.header_loop:
            logger_verbose.debug(f"{self.prefix} self.header_loop true")
            if self.header_loop.running:
                logger_verbose.debug(f"{self.prefix} stop_header_loop, calling stop")
                self.header_loop.stop()
        if cancel and self.header_loop_deferred:
            logger_verbose.debug(f"{self.prefix} stop_header_loop: trying to cancel")
            self.header_loop_deferred.cancel()

    def __init__(self, incoming_client=False):
        """
        Create an instance.
        The NeoNode class is the equivalent of the C# RemoteNode.cs class. It represents a single Node connected to the client.

        Args:
            incoming_client (bool): True if node is an incoming client and the handshake should be initiated.
        """
        from neo.Network.NodeLeader import NodeLeader

        self.leader = NodeLeader.Instance()
        self.nodeid = self.leader.NodeId
        self.remote_nodeid = random.randint(1294967200, 4294967200)
        self.endpoint = ''
        self.address = None
        self.buffer_in = bytearray()
        self.myblockrequests = set()
        self.bytes_in = 0
        self.bytes_out = 0

        self.sync_mode = MODE_CATCHUP

        self.host = None
        self.port = None

        self.incoming_client = incoming_client
        self.handshake_complete = False
        self.expect_verack_next = False
        self.start_outstanding_data_request = {HEARTBEAT_BLOCKS: 0, HEARTBEAT_HEADERS: 0}

        self.block_loop = None
        self.block_loop_deferred = None

        self.peer_loop = None
        self.peer_loop_deferred = None

        self.header_loop = None
        self.header_loop_deferred = None

        self.disconnect_deferred = None
        self.disconnecting = False

        logger.debug(f"{self.prefix} new node created, not yet connected")

    def Disconnect(self, reason=None, isDead=True):
        """Close the connection with the remote node client."""
        self.disconnecting = True
        self.expect_verack_next = False
        if reason:
            logger.debug(f"Disconnecting with reason: {reason}")
        self.stop_block_loop()
        self.stop_header_loop()
        self.stop_peerinfo_loop()
        if isDead:
            self.leader.AddDeadAddress(self.address, reason=f"{self.prefix} Forced disconnect by us")

        self.leader.forced_disconnect_by_us += 1

        self.disconnect_deferred = defer.Deferred()
        self.disconnect_deferred.debug = True
        # force disconnection without waiting on the other side
        # calling later to give func caller time to add callbacks to the deferred
        reactor.callLater(1, self.transport.abortConnection)
        return self.disconnect_deferred

    @property
    def prefix(self):
        if isinstance(self.endpoint, IPv4Address) and self.identifier is not None:
            return f"[{self.identifier:03}][{mode_to_name[self.sync_mode]}][{self.address:>21}]"
        else:
            return f""

    def Name(self):
        """
        Get the peer name.

        Returns:
            str:
        """
        name = ""
        if self.Version:
            name = self.Version.UserAgent
        return name

    def GetNetworkAddressWithTime(self):
        """
        Get a network address object.

        Returns:
            NetworkAddressWithTime: if we have a connection to a node.
            None: otherwise.
        """
        if self.port is not None and self.host is not None and self.Version is not None:
            return NetworkAddressWithTime(self.host, self.port, self.Version.Services)
        return None

    def IOStats(self):
        """
        Get the connection I/O stats.

        Returns:
            str:
        """
        biM = self.bytes_in / 1000000  # megabyes
        boM = self.bytes_out / 1000000

        return f"{biM:>10} MB in / {boM:>10} MB out"

    def connectionMade(self):
        """Callback handler from twisted when establishing a new connection."""
        self.endpoint = self.transport.getPeer()
        # get the reference to the Address object in NodeLeader so we can manipulate it properly.
        tmp_addr = Address(f"{self.endpoint.host}:{self.endpoint.port}")
        try:
            known_idx = self.leader.KNOWN_ADDRS.index(tmp_addr)
            self.address = self.leader.KNOWN_ADDRS[known_idx]
        except ValueError:
            # Not found.
            self.leader.AddKnownAddress(tmp_addr)
            self.address = tmp_addr

        self.address.address = "%s:%s" % (self.endpoint.host, self.endpoint.port)
        self.host = self.endpoint.host
        self.port = int(self.endpoint.port)
        self.leader.AddConnectedPeer(self)
        self.leader.RemoveFromQueue(self.address)
        self.leader.peers_connecting -= 1
        logger.debug(f"{self.address} connection established")
        if self.incoming_client:
            # start protocol
            self.SendVersion()

    def connectionLost(self, reason=None):
        """Callback handler from twisted when a connection was lost."""
        try:
            self.connected = False
            self.stop_block_loop()
            self.stop_peerinfo_loop()
            self.stop_header_loop()

            self.ReleaseBlockRequests()
            self.leader.RemoveConnectedPeer(self)

            time_expired = self.time_expired(HEARTBEAT_BLOCKS)
            # some NEO-cli versions have a 30s timeout to receive block/consensus or tx messages. By default neo-python doesn't respond to these requests
            if time_expired > 20:
                self.address.last_connection = Address.Now()
                self.leader.AddDeadAddress(self.address, reason=f"{self.prefix} Premature disconnect")

            if reason and reason.check(twisted_error.ConnectionDone):
                # this might happen if they close our connection because they've reached max peers or something similar
                logger.debug(f"{self.prefix} disconnected normally with reason:{reason.value}")
                self._check_for_consecutive_disconnects("connection done")

            elif reason and reason.check(twisted_error.ConnectionLost):
                # Can be due to a timeout. Only if this happened again within 5 minutes do we label the node as bad
                # because then it clearly doesn't want to talk to us or we have a bad connection to them.
                # Otherwise allow for the node to be queued again by NodeLeader.
                logger.debug(f"{self.prefix} disconnected with connectionlost reason: {reason.value}")
                self._check_for_consecutive_disconnects("connection lost")

            else:
                logger.debug(f"{self.prefix} disconnected with reason: {reason.value}")
        except Exception as e:
            logger.error("Error with connection lost: %s " % e)

        def try_me(err):
            err.check(error.ConnectionAborted)

        if self.disconnect_deferred:
            d, self.disconnect_deferred = self.disconnect_deferred, None  # type: defer.Deferred
            d.addErrback(try_me)
            if len(d.callbacks) > 0:
                d.callback(reason)
            else:
                print("connLost, disconnect_deferred cancelling!")
                d.cancel()

    def _check_for_consecutive_disconnects(self, error_name):
        now = datetime.datetime.utcnow().timestamp()
        FIVE_MINUTES = 5 * 60
        if self.address.last_connection != 0 and now - self.address.last_connection < FIVE_MINUTES:
            self.leader.AddDeadAddress(self.address, reason=f"{self.prefix} second {error_name} within 5 minutes")
        else:
            self.address.last_connection = Address.Now()

    def ReleaseBlockRequests(self):
        bcr = BC.Default().BlockRequests
        requests = self.myblockrequests

        for req in requests:
            try:
                if req in bcr:
                    bcr.remove(req)
            except Exception as e:
                logger.debug(f"{self.prefix} Could not remove request {e}")

        self.myblockrequests = set()

    def dataReceived(self, data):
        """ Called from Twisted whenever data is received. """
        self.bytes_in += (len(data))
        self.buffer_in = self.buffer_in + data

        while self.CheckDataReceived():
            pass

    def CheckDataReceived(self):
        """Tries to extract a Message from the data buffer and process it."""
        currentLength = len(self.buffer_in)
        if currentLength < 24:
            return False
        # Extract the message header from the buffer, and return if not enough
        # buffer to fully deserialize the message object.

        try:
            # Construct message
            mstart = self.buffer_in[:24]
            ms = StreamManager.GetStream(mstart)
            reader = BinaryReader(ms)
            m = Message()

            # Extract message metadata
            m.Magic = reader.ReadUInt32()
            m.Command = reader.ReadFixedString(12).decode('utf-8')
            m.Length = reader.ReadUInt32()
            m.Checksum = reader.ReadUInt32()

            # Return if not enough buffer to fully deserialize object.
            messageExpectedLength = 24 + m.Length
            if currentLength < messageExpectedLength:
                return False

        except Exception as e:
            logger.debug(f"{self.prefix} Error: could not read message header from stream {e}")
            # self.Log('Error: Could not read initial bytes %s ' % e)
            return False

        finally:
            StreamManager.ReleaseStream(ms)
            del reader

        # The message header was successfully extracted, and we have enough enough buffer
        # to extract the full payload
        try:
            # Extract message bytes from buffer and truncate buffer
            mdata = self.buffer_in[:messageExpectedLength]
            self.buffer_in = self.buffer_in[messageExpectedLength:]

            # Deserialize message with payload
            stream = StreamManager.GetStream(mdata)
            reader = BinaryReader(stream)
            message = Message()
            message.Deserialize(reader)

            if self.incoming_client and self.expect_verack_next:
                if message.Command != 'verack':
                    self.Disconnect("Expected 'verack' got {}".format(message.Command))

            # Propagate new message
            self.MessageReceived(message)

        except Exception as e:
            logger.debug(f"{self.prefix} Could not extract message {e}")
            # self.Log('Error: Could not extract message: %s ' % e)
            return False

        finally:
            StreamManager.ReleaseStream(stream)

        return True

    def MessageReceived(self, m):
        """
        Process a message.

        Args:
            m (neo.Network.Message):
        """
        if m.Command == 'verack':
            # only respond with a verack when we connect to another client, not when a client connected to us or
            # we might end up in a verack loop
            if self.incoming_client:
                if self.expect_verack_next:
                    self.expect_verack_next = False
            else:
                self.HandleVerack()
        elif m.Command == 'version':
            self.HandleVersion(m.Payload)
        elif m.Command == 'getaddr':
            self.SendPeerInfo()
        elif m.Command == 'getdata':
            self.HandleGetDataMessageReceived(m.Payload)
        elif m.Command == 'getblocks':
            self.HandleGetBlocksMessageReceived(m.Payload)
        elif m.Command == 'inv':
            self.HandleInvMessage(m.Payload)
        elif m.Command == 'block':
            self.HandleBlockReceived(m.Payload)
        elif m.Command == 'getheaders':
            self.HandleGetHeadersMessageReceived(m.Payload)
        elif m.Command == 'headers':
            self.HandleBlockHeadersReceived(m.Payload)
        elif m.Command == 'addr':
            self.HandlePeerInfoReceived(m.Payload)
        else:
            logger.debug(f"{self.prefix} Command not implemented: {m.Command}")

    def OnLoopError(self, err):
        # happens if we cancel the disconnect_deferred before it is executed
        # causes no harm
        if type(err.value) == CancelledError:
            logger_verbose.debug(f"{self.prefix} OnLoopError cancelled deferred")
            return
        logger.debug(f"{self.prefix} On neo Node loop error {err}")

    def onThreadDeferredErr(self, err):
        if type(err.value) == CancelledError:
            logger_verbose.debug(f"{self.prefix} onThreadDeferredError cancelled deferred")
            return
        logger.debug(f"{self.prefix} On Call from thread error {err}")

    def keep_alive(self):
        ka = Message("ping")
        self.SendSerializedMessage(ka)

    def ProtocolReady(self):
        # do not start the looping tasks if we're in the BlockRequests catchup task
        # otherwise BCRLen will not drop because the new node will continue adding blocks
        logger_verbose.debug(f"{self.prefix} ProtocolReady called")
        if not self.leader.check_bcr_loop or (self.leader.check_bcr_loop and not self.leader.check_bcr_loop.running):
            logger_verbose.debug(f"{self.prefix} Protocol ready -> starting loops")
            self.start_block_loop()
            self.start_peerinfo_loop()
            self.start_header_loop()

        self.RequestPeerInfo()

    def AskForMoreHeaders(self):
        logger.debug(f"{self.prefix} asking for more headers, starting from {BC.Default().HeaderHeight}")
        self.health_check(HEARTBEAT_HEADERS)
        get_headers_message = Message("getheaders", GetBlocksPayload(hash_start=[BC.Default().CurrentHeaderHash]))
        self.SendSerializedMessage(get_headers_message)

    def AskForMoreBlocks(self):

        distance = BC.Default().HeaderHeight - BC.Default().Height

        current_mode = self.sync_mode

        if distance > 2000:
            self.sync_mode = MODE_CATCHUP
        else:
            self.sync_mode = MODE_MAINTAIN

        if self.sync_mode != current_mode:
            logger.debug(f"{self.prefix} changing sync_mode to {mode_to_name[self.sync_mode]}")
            self.stop_block_loop()
            self.start_block_loop()

        else:
            if len(BC.Default().BlockRequests) > self.leader.BREQMAX:
                logger.debug(f"{self.prefix} data request speed exceeding node response rate...pausing to catch up")
                self.leader.throttle_sync()
            else:
                self.DoAskForMoreBlocks()

    def DoAskForMoreBlocks(self):
        hashes = []
        hashstart = BC.Default().Height + 1
        current_header_height = BC.Default().HeaderHeight + 1

        do_go_ahead = False
        if BC.Default().BlockSearchTries > 100 and len(BC.Default().BlockRequests) > 0:
            do_go_ahead = True

        first = None
        while hashstart <= current_header_height and len(hashes) < self.leader.BREQPART:
            hash = BC.Default().GetHeaderHash(hashstart)
            if not do_go_ahead:
                if hash is not None and hash not in BC.Default().BlockRequests \
                        and hash not in self.myblockrequests:

                    if not first:
                        first = hashstart
                    BC.Default().BlockRequests.add(hash)
                    self.myblockrequests.add(hash)
                    hashes.append(hash)
            else:
                if hash is not None:
                    if not first:
                        first = hashstart
                    BC.Default().BlockRequests.add(hash)
                    self.myblockrequests.add(hash)
                    hashes.append(hash)

            hashstart += 1

        if len(hashes) > 0:
            logger.debug(
                f"{self.prefix} asking for more blocks {first} - {hashstart} ({len(hashes)}) stale count: {BC.Default().BlockSearchTries} "
                f"BCRLen: {len(BC.Default().BlockRequests)}")
            self.health_check(HEARTBEAT_BLOCKS)
            message = Message("getdata", InvPayload(InventoryType.Block, hashes))
            self.SendSerializedMessage(message)

    def RequestPeerInfo(self):
        """Request the peer address information from the remote client."""
        logger.debug(f"{self.prefix} requesting peer info")
        self.SendSerializedMessage(Message('getaddr'))

    def HandlePeerInfoReceived(self, payload):
        """Process response of `self.RequestPeerInfo`."""
        addrs = IOHelper.AsSerializableWithType(payload, 'neo.Network.Payloads.AddrPayload.AddrPayload')

        if not addrs:
            return

        for nawt in addrs.NetworkAddressesWithTime:
            self.leader.RemoteNodePeerReceived(nawt.Address, nawt.Port, self.prefix)

    def SendPeerInfo(self):
        # if not self.leader.ServiceEnabled:
        #     return

        peerlist = []
        for peer in self.leader.Peers:
            addr = peer.GetNetworkAddressWithTime()
            if addr is not None:
                peerlist.append(addr)
        peer_str_list = list(map(lambda p: p.ToString(), peerlist))
        logger.debug(f"{self.prefix} Sending Peer list {peer_str_list}")

        addrpayload = AddrPayload(addresses=peerlist)
        message = Message('addr', addrpayload)
        self.SendSerializedMessage(message)

    def RequestVersion(self):
        """Request the remote client version."""
        m = Message("getversion")
        self.SendSerializedMessage(m)

    def SendVersion(self):
        """Send our client version."""
        m = Message("version", VersionPayload(settings.NODE_PORT, self.remote_nodeid, settings.VERSION_NAME))
        self.SendSerializedMessage(m)

    def SendVerack(self):
        """Send version acknowledge"""
        m = Message('verack')
        self.SendSerializedMessage(m)
        self.expect_verack_next = True

    def HandleVersion(self, payload):
        """Process the response of `self.RequestVersion`."""
        self.Version = IOHelper.AsSerializableWithType(payload, "neo.Network.Payloads.VersionPayload.VersionPayload")

        if not self.Version:
            return

        if self.incoming_client:
            if self.Version.Nonce == self.nodeid:
                self.Disconnect()
            self.SendVerack()
        else:
            self.nodeid = self.Version.Nonce
            self.SendVersion()

    def HandleVerack(self):
        """Handle the `verack` response."""
        m = Message('verack')
        self.SendSerializedMessage(m)
        self.leader.NodeCount += 1
        self.identifier = self.leader.NodeCount
        logger.debug(f"{self.prefix} Handshake complete!")
        self.handshake_complete = True
        self.ProtocolReady()

    def HandleInvMessage(self, payload):
        """
        Process a block header inventory payload.

        Args:
            inventory (neo.Network.Payloads.InvPayload):
        """

        if self.sync_mode != MODE_MAINTAIN:
            return

        inventory = IOHelper.AsSerializableWithType(payload, 'neo.Network.Payloads.InvPayload.InvPayload')
        if not inventory:
            return

        if inventory.Type == InventoryType.BlockInt:

            ok_hashes = []
            for hash in inventory.Hashes:
                hash = hash.encode('utf-8')
                if hash not in self.myblockrequests and hash not in BC.Default().BlockRequests:
                    ok_hashes.append(hash)
                    BC.Default().BlockRequests.add(hash)
                    self.myblockrequests.add(hash)
            if len(ok_hashes):
                message = Message("getdata", InvPayload(InventoryType.Block, ok_hashes))
                self.SendSerializedMessage(message)

        elif inventory.Type == InventoryType.TXInt:
            pass
        elif inventory.Type == InventoryType.ConsensusInt:
            pass

    def SendSerializedMessage(self, message):
        """
        Send the `message` to the remote client.

        Args:
            message (neo.Network.Message):
        """
        try:
            ba = Helper.ToArray(message)
            ba2 = binascii.unhexlify(ba)
            self.bytes_out += len(ba2)
            self.transport.write(ba2)
        except Exception as e:
            logger.debug(f"Could not send serialized message {e}")

    def HandleBlockHeadersReceived(self, inventory):
        """
        Process a block header inventory payload.

        Args:
            inventory (neo.Network.Inventory):
        """
        try:
            inventory = IOHelper.AsSerializableWithType(inventory, 'neo.Network.Payloads.HeadersPayload.HeadersPayload')
            if inventory is not None:
                logger.debug(f"{self.prefix} received headers")
                self.heart_beat(HEARTBEAT_HEADERS)
                BC.Default().AddHeaders(inventory.Headers)

        except Exception as e:
            logger.debug(f"Error handling Block headers {e}")

    def HandleBlockReceived(self, inventory):
        """
        Process a Block inventory payload.

        Args:
            inventory (neo.Network.Inventory):
        """
        block = IOHelper.AsSerializableWithType(inventory, 'neo.Core.Block.Block')
        if not block:
            return

        blockhash = block.Hash.ToBytes()
        try:
            if blockhash in BC.Default().BlockRequests:
                BC.Default().BlockRequests.remove(blockhash)
        except KeyError:
            pass
        try:
            if blockhash in self.myblockrequests:
                # logger.debug(f"{self.prefix} received block: {block.Index}")
                self.heart_beat(HEARTBEAT_BLOCKS)
                self.myblockrequests.remove(blockhash)
        except KeyError:
            pass
        self.leader.InventoryReceived(block)

    def time_expired(self, what):
        now = datetime.datetime.utcnow().timestamp()
        start_time = self.start_outstanding_data_request.get(what)
        if start_time == 0:
            delta = 0
        else:
            delta = now - start_time
        return delta

    def health_check(self, what):
        # now = datetime.datetime.utcnow().timestamp()
        # delta = now - self.start_outstanding_data_request.get(what)

        time_expired = self.time_expired(what)

        if time_expired == 0:
            # startup scenario, just go
            logger.debug(f"{self.prefix}[HEALTH][{what}] startup or bcr catchup heart_beat")
            self.heart_beat(what)
        else:
            if self.sync_mode == MODE_CATCHUP:
                response_threshold = 45  # seconds
            else:
                response_threshold = 90  #
            if time_expired > response_threshold:
                header_time = self.time_expired(HEARTBEAT_HEADERS)
                header_bad = header_time > response_threshold
                block_time = self.time_expired(HEARTBEAT_BLOCKS)
                blocks_bad = block_time > response_threshold
                if header_bad and blocks_bad:
                    logger.debug(
                        f"{self.prefix}[HEALTH] FAILED - No response for Headers {header_time:.2f} and Blocks {block_time:.2f} seconds. Removing node...")
                    self.Disconnect()
                elif blocks_bad and self.leader.check_bcr_loop and self.leader.check_bcr_loop.running:
                    # when we're in data throttling it is never acceptable if blocks don't come in. 
                    logger.debug(
                        f"{self.prefix}[HEALTH] FAILED - No Blocks for {block_time:.2f} seconds while throttling. Removing node...")
                    self.Disconnect()
                else:
                    if header_bad:
                        logger.debug(
                            f"{self.prefix}[HEALTH] Headers FAILED @ {header_time:.2f}s, but Blocks OK @ {block_time:.2f}s. Keeping node...")
                    else:
                        logger.debug(
                            f"{self.prefix}[HEALTH] Headers OK @ {header_time:.2f}s, but Blocks FAILED @ {block_time:.2f}s. Keeping node...")

                # logger.debug(
                #     f"{self.prefix}[HEALTH][{what}] FAILED - No response for {time_expired:.2f} seconds. Removing node...")

            else:
                logger.debug(f"{self.prefix}[HEALTH][{what}] OK - response time {time_expired:.2f}")

    def heart_beat(self, what):
        self.start_outstanding_data_request[what] = datetime.datetime.utcnow().timestamp()

    def HandleGetHeadersMessageReceived(self, payload):

        if not self.leader.ServiceEnabled:
            return

        inventory = IOHelper.AsSerializableWithType(payload, 'neo.Network.Payloads.GetBlocksPayload.GetBlocksPayload')

        if not inventory:
            return

        blockchain = BC.Default()

        hash = inventory.HashStart[0]

        if hash is None or hash == inventory.HashStop:
            logger.debug("getheaders: Hash {} not found or hashstop reached".format(inventory.HashStart))
            return

        headers = []
        header_count = 0

        while hash != inventory.HashStop and header_count < 2000:
            hash = blockchain.GetNextBlockHash(hash)
            if not hash:
                break
            headers.append(blockchain.GetHeader(hash))
            header_count += 1

        if header_count > 0:
            self.SendSerializedMessage(Message('headers', HeadersPayload(headers=headers)))

    def HandleBlockReset(self, hash):
        """Process block reset request."""
        self.myblockrequests = set()

    def HandleGetDataMessageReceived(self, payload):
        """
        Process a InvPayload payload.

        Args:
            payload (neo.Network.Inventory):
        """
        inventory = IOHelper.AsSerializableWithType(payload, 'neo.Network.Payloads.InvPayload.InvPayload')
        if not inventory:
            return

        for hash in inventory.Hashes:
            hash = hash.encode('utf-8')

            item = None
            # try to get the inventory to send from relay cache

            if hash in self.leader.RelayCache.keys():
                item = self.leader.RelayCache[hash]

            if inventory.Type == InventoryType.TXInt:
                if not item:
                    item, index = BC.Default().GetTransaction(hash)
                if not item:
                    item = self.leader.GetTransaction(hash)
                if item:
                    message = Message(command='tx', payload=item, print_payload=False)
                    self.SendSerializedMessage(message)

            elif inventory.Type == InventoryType.BlockInt:
                if not item:
                    item = BC.Default().GetBlock(hash)
                if item:
                    message = Message(command='block', payload=item, print_payload=False)
                    self.SendSerializedMessage(message)

            elif inventory.Type == InventoryType.ConsensusInt:
                if item:
                    self.SendSerializedMessage(Message(command='consensus', payload=item, print_payload=False))

    def HandleGetBlocksMessageReceived(self, payload):
        """
        Process a GetBlocksPayload payload.

        Args:
            payload (neo.Network.Payloads.GetBlocksPayload):
        """
        if not self.leader.ServiceEnabled:
            return

        inventory = IOHelper.AsSerializableWithType(payload, 'neo.Network.Payloads.GetBlocksPayload.GetBlocksPayload')
        if not inventory:
            return

        blockchain = BC.Default()
        hash = inventory.HashStart[0]
        if not blockchain.GetHeader(hash):
            return

        hashes = []
        hcount = 0
        while hash != inventory.HashStop and hcount < 500:
            hash = blockchain.GetNextBlockHash(hash)
            if hash is None:
                break
            hashes.append(hash)
            hcount += 1
        if hcount > 0:
            self.SendSerializedMessage(Message('inv', InvPayload(type=InventoryType.Block, hashes=hashes)))

    def Relay(self, inventory):
        """
        Wrap the inventory in a InvPayload object and send it over the write to the remote node.

        Args:
            inventory:

        Returns:
            bool: True (fixed)
        """
        inventory = InvPayload(type=inventory.InventoryType, hashes=[inventory.Hash.ToBytes()])
        m = Message("inv", inventory)
        self.SendSerializedMessage(m)

        return True

    def __eq__(self, other):
        if type(other) is type(self):
            return self.address == other.address and self.identifier == other.identifier
        else:
            return False
