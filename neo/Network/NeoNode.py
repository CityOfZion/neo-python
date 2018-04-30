import binascii
import random
from logzero import logger
from twisted.internet.protocol import Protocol
from twisted.internet import reactor, task
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
from .InventoryType import InventoryType
from neo.Settings import settings


MODE_MAINTAIN = 7
MODE_CATCHUP = 2


class NeoNode(Protocol):
    Version = None

    leader = None

    block_loop = None

    peer_loop = None

    sync_mode = MODE_CATCHUP

    identifier = None

    def __init__(self):
        """
        Create an instance.
        The NeoNode class is the equivalent of the C# RemoteNode.cs class. It represents a single Node connected to the client.
        """
        from neo.Network.NodeLeader import NodeLeader

        self.leader = NodeLeader.Instance()
        self.nodeid = self.leader.NodeId
        self.remote_nodeid = random.randint(1294967200, 4294967200)
        self.endpoint = ''
        self.buffer_in = bytearray()
        self.myblockrequests = set()
        self.bytes_in = 0
        self.bytes_out = 0

        self.host = None
        self.port = None
        self.identifier = self.leader.NodeCount
        self.leader.NodeCount += 1

        self.Log("New Node created %s " % self.identifier)

    def Disconnect(self):
        """Close the connection with the remote node client."""
        self.transport.loseConnection()

    @property
    def Address(self):
        if self.endpoint:
            return "%s:%s" % (self.endpoint.host, self.endpoint.port)
        return ""

    def Name(self):
        """
        Get the peer name.

        Returns:
            str:
        """
        return self.transport.getPeer()

    def GetNetworkAddressWithTime(self):
        """
        Get a network address object.

        Returns:
            NetworkAddressWithTime: if we have a connection to a node.
            None: otherwise.
        """
        if self.port is not None and self.host is not None:
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

        return "%s MB in / %s MB out" % (biM, boM)

    def connectionMade(self):
        """Callback handler from twisted when establishing a new connection."""
        self.endpoint = self.transport.getPeer()
        self.host = self.endpoint.host
        self.port = int(self.endpoint.port)
        self.leader.AddConnectedPeer(self)
        self.Log("Connection from %s" % self.endpoint)

    def connectionLost(self, reason=None):
        """Callback handler from twisted when a connection was lost."""
        if self.block_loop:
            self.block_loop.stop()
            self.block_loop = None
        if self.peer_loop:
            self.peer_loop.stop()
            self.peer_loop = None

        self.ReleaseBlockRequests()
        self.leader.RemoveConnectedPeer(self)
        self.Log("%s disconnected %s" % (self.remote_nodeid, reason))

    def ReleaseBlockRequests(self):
        bcr = BC.Default().BlockRequests
        requests = self.myblockrequests

        for req in requests:
            try:
                if req in bcr:
                    bcr.remove(req)
            except Exception as e:
                self.Log("Could not remove request %s " % e)

        self.myblockrequests = set()

    def dataReceived(self, data):
        """ Called from Twisted whenever data is received. """
        self.bytes_in += (len(data))
        self.buffer_in = self.buffer_in + data
        self.CheckDataReceived()

    def CheckDataReceived(self):
        """Tries to extract a Message from the data buffer and process it."""
        currentLength = len(self.buffer_in)
        if currentLength < 24:
            return

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
                return

        except Exception as e:
            self.Log('Error: Could not read initial bytes %s ' % e)
            return

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

            # Propagate new message
            self.MessageReceived(message)

        except Exception as e:
            self.Log('Error: Could not extract message: %s ' % e)
            return

        finally:
            StreamManager.ReleaseStream(stream)

        # Finally, after a message has been fully deserialized and propagated,
        # check if another message can be extracted with the current buffer:
        if len(self.buffer_in) >= 24:
            self.CheckDataReceived()

    def MessageReceived(self, m):
        """
        Process a message.

        Args:
            m (neo.Network.Message):
        """

        if m.Command == 'verack':
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
        elif m.Command == 'headers':
            reactor.callFromThread(self.HandleBlockHeadersReceived, m.Payload)
        #            self.HandleBlockHeadersReceived(m.Payload)
        elif m.Command == 'addr':
            self.HandlePeerInfoReceived(m.Payload)
        else:
            self.Log("Command %s not implemented " % m.Command)

    def ProtocolReady(self):
        self.AskForMoreHeaders()

        self.block_loop = task.LoopingCall(self.AskForMoreBlocks)
        self.block_loop.start(self.sync_mode)

        # ask every 3 minutes for new peers
        self.peer_loop = task.LoopingCall(self.RequestPeerInfo)
        self.peer_loop.start(120, now=False)

    def AskForMoreHeaders(self):
        # self.Log("asking for more headers...")
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
            self.block_loop.stop()
            # self.Log("Changing sync mode from %s to %s" % (current_mode, self.sync_mode))
            self.block_loop.start(self.sync_mode)
        else:
            if len(BC.Default().BlockRequests) > self.leader.BREQMAX:
                self.leader.ResetBlockRequestsAndCache()

            self.DoAskForMoreBlocks()

    def DoAskForMoreBlocks(self):
        hashes = []
        hashstart = BC.Default().Height + 1
        current_header_height = BC.Default().HeaderHeight + 1

        do_go_ahead = False
        if BC.Default().BlockSearchTries > 100 and len(BC.Default().BlockRequests) > 0:
            do_go_ahead = True

        first = None
        while hashstart < current_header_height and len(hashes) < self.leader.BREQPART:
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
                if not first:
                    first = hashstart
                BC.Default().BlockRequests.add(hash)
                self.myblockrequests.add(hash)
                hashes.append(hash)

            hashstart += 1

        self.Log("asked for more blocks ... %s thru %s (%s blocks) stale count %s BCRLen: %s " % (first, hashstart, len(hashes), BC.Default().BlockSearchTries, len(BC.Default().BlockRequests)))

        if len(hashes) > 0:
            message = Message("getdata", InvPayload(InventoryType.Block, hashes))
            reactor.callInThread(self.SendSerializedMessage, message)

    def RequestPeerInfo(self):
        """Request the peer address information from the remote client."""
        self.SendSerializedMessage(Message('getaddr'))

    def HandlePeerInfoReceived(self, payload):
        """Process response of `self.RequestPeerInfo`."""
        addrs = IOHelper.AsSerializableWithType(payload, 'neo.Network.Payloads.AddrPayload.AddrPayload')

        for index, nawt in enumerate(addrs.NetworkAddressesWithTime):
            self.leader.RemoteNodePeerReceived(nawt.Address, nawt.Port, index)

    def SendPeerInfo(self):

        #        self.Log("SENDING PEER INFO %s " % self)

        #        peerlist = []
        #        for peer in self.leader.Peers:
        #            peerlist.append( peer.GetNetworkAddressWithTime())
        #        self.Log("Peer list %s " % peerlist)

        #        addrpayload = AddrPayload(addresses=peerlist)
        #        message = Message('addr',addrpayload)
        #        self.SendSerializedMessage(message)
        #       dont send peer info now
        pass

    def RequestVersion(self):
        """Request the remote client version."""
        # self.Log("All caught up, requesting version")
        m = Message("getversion")
        self.SendSerializedMessage(m)

    def SendVersion(self):
        """Send our client version."""
        m = Message("version", VersionPayload(settings.NODE_PORT, self.remote_nodeid, settings.VERSION_NAME))
        self.SendSerializedMessage(m)

    def HandleVersion(self, payload):
        """Process the response of `self.RequestVersion`."""
        self.Version = IOHelper.AsSerializableWithType(payload, "neo.Network.Payloads.VersionPayload.VersionPayload")
        self.nodeid = self.Version.Nonce
#        self.Log("Remote version %s " % vars(self.Version))
        self.SendVersion()

    def HandleVerack(self):
        """Handle the `verack` response."""
        m = Message('verack')
        self.SendSerializedMessage(m)
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

        if inventory.Type == InventoryType.BlockInt:

            ok_hashes = []
            for hash in inventory.Hashes:
                hash = hash.encode('utf-8')
                if hash not in self.myblockrequests and hash not in BC.Default().BlockRequests:
                    ok_hashes.append(hash)
                    BC.Default().BlockRequests.add(hash)
                    self.myblockrequests.add(hash)
            if len(ok_hashes):
                #                logger.info("OK HASHES, get data %s " % ok_hashes)
                message = Message("getdata", InvPayload(InventoryType.Block, ok_hashes))
                self.SendSerializedMessage(message)

        elif inventory.Type == InventoryType.TXInt:
            pass
        elif inventory.Type == InventoryType.ConsensusInt:
            pass

#        for hash in inventory.Hashes:
#            if not hash in self.leader.KnownHashes:
#                if not hash in self.leader.MissionsGlobal:
#                    self.leader.MissionsGlobal.append(hash)

    def SendSerializedMessage(self, message):
        """
        Send the `message` to the remote client.

        Args:
            message (neo.Network.Message):
        """
        ba = Helper.ToArray(message)
        ba2 = binascii.unhexlify(ba)
        self.bytes_out += len(ba2)
        self.transport.write(ba2)

    def HandleBlockHeadersReceived(self, inventory):
        """
        Process a block header inventory payload.

        Args:
            inventory (neo.Network.Inventory):
        """
        inventory = IOHelper.AsSerializableWithType(inventory, 'neo.Network.Payloads.HeadersPayload.HeadersPayload')
#        self.Log("Received headers %s " % ([h.Hash.ToBytes() for h in inventory.Headers]))
        if inventory is not None:
            BC.Default().AddHeaders(inventory.Headers)

        if BC.Default().HeaderHeight < self.Version.StartHeight:
            self.AskForMoreHeaders()
        else:
            reactor.callLater(5, self.AskForMoreHeaders)

    def HandleBlockReceived(self, inventory):
        """
        Process a Block inventory payload.

        Args:
            inventory (neo.Network.Inventory):
        """
        block = IOHelper.AsSerializableWithType(inventory, 'neo.Core.Block.Block')

        blockhash = block.Hash.ToBytes()
        if blockhash in BC.Default().BlockRequests:
            BC.Default().BlockRequests.remove(blockhash)
        if blockhash in self.myblockrequests:
            self.myblockrequests.remove(blockhash)

        self.leader.InventoryReceived(block)

    def HandleBlockReset(self, hash):
        """Process block reset request."""
        self.myblockrequests = []

    def HandleGetDataMessageReceived(self, payload):
        """
        Process a InvPayload payload.

        Args:
            payload (neo.Network.Inventory):
        """
        inventory = IOHelper.AsSerializableWithType(payload, 'neo.Network.Payloads.InvPayload.InvPayload')

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
                    message = Message(command='block', payload=item, print_payload=True)
                    self.SendSerializedMessage(message)

            elif inventory.Type == InventoryType.ConsensusInt:
                if item:
                    self.SendSerializedMessage(Message(command='consensus', payload=item, print_payload=True))

    def HandleGetBlocksMessageReceived(self, payload):
        """
        Process a GetBlocksPayload payload.

        Args:
            payload (neo.Network.Payloads.GetBlocksPayload):
        """
        if not self.leader.ServiceEnabled:
            return

        inventory = IOHelper.AsSerializableWithType(payload, 'neo.Network.Payloads.GetBlocksPayload.GetBlocksPayload')

        if not BC.Default().GetHeader(inventory.HashStart):
            self.Log("Hash %s not found %s " % inventory.HashStart)
            return

        hashes = []
        hcount = 0
        hash = inventory.HashStart
        while hash != inventory.HashStop and hcount < 500:
            hash = BC.Default().GetNextBlockHash(hash)
            if hash is None:
                break
            hashes.append(hash)
            hcount += 1
        if hcount > 0:
            self.Log("sending inv hashes! %s " % hashes)
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

    def Log(self, msg):
        logger.debug("[%s][mode %s] %s - %s" % (self.identifier, self.sync_mode, self.endpoint, msg))
