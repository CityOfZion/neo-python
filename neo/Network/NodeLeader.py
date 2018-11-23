import random
import time
from neo.Core.Block import Block
from neo.Core.Blockchain import Blockchain as BC
from neo.Implementations.Blockchains.LevelDB.TestLevelDBBlockchain import TestLevelDBBlockchain
from neo.Core.TX.Transaction import Transaction
from neo.Core.TX.MinerTransaction import MinerTransaction
from neo.Network.NeoNode import NeoNode, HEARTBEAT_BLOCKS
from neo.Settings import settings
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor, task
from twisted.internet.defer import CancelledError
from neo.logging import log_manager
from neo.Network.address import Address

logger = log_manager.getLogger('network')
log_manager.config_stdio([('network', 10)])


class NeoClientFactory(ReconnectingClientFactory):
    maxRetries = 1

    def __init__(self, incoming_client=False):
        """

        Args:
            incoming_client (bool): true to create a NeoNode for an incoming client that initiates the P2P handshake.
        """
        self.incoming = incoming_client
        super(NeoClientFactory, self).__init__()

    def buildProtocol(self, addr):
        return NeoNode(self.incoming)

    def clientConnectionFailed(self, connector, reason):
        address = Address("%s:%s" % (connector.host, connector.port), Address.Now())
        logger.debug(f"Failed connecting to {address} {reason}")
        leader = NodeLeader.Instance()
        if "Connection refused" in str(reason) or "Operation timed out" in str(reason):
            try:
                if address in leader.KNOWN_ADDRS:
                    leader.KNOWN_ADDRS.remove(address)
                # try removing
                leader.RemoveFromQueue(address)
                # if we failed to connect to new addresses, we should always add them to the DEAD_ADDRS list
                if address not in leader.DEAD_ADDRS:
                    logger.debug(f"Adding address {address:>21} to DEAD_ADDRS list")
                    leader.DEAD_ADDRS.append(address)
            except KeyError:
                logger.error(
                    f"clientConnectionFailed tried to remove something that wasn't there {address} {leader.ADDRS} {leader.connection_queue} {leader.DEAD_ADDRS}")

    def clientConnectionLost(self, connector, reason):
        address = Address("%s:%s" % (connector.host, connector.port), Address.Now())
        logger.debug("Dropped connection from %s " % address)
        for peer in NodeLeader.Instance().Peers:
            if peer.Address == address:
                peer.connectionLost()


class NodeLeader:
    _LEAD = None

    Peers = []

    UnconnectedPeers = []

    KNOWN_ADDRS = []
    DEAD_ADDRS = []

    NodeId = None

    _MissedBlocks = []

    BREQPART = 100
    BREQMAX = 10000

    KnownHashes = []
    MissionsGlobal = []
    MemPool = {}
    RelayCache = {}

    NodeCount = 0

    CurrentBlockheight = 0

    ServiceEnabled = False

    peer_check_loop = None
    peer_check_loop_deferred = None

    check_bcr_loop = None
    check_bcr_loop_deferred = None

    memcheck_loop = None
    memcheck_loop_deferred = None

    blockheight_loop = None
    blockheight_loop_deferred = None

    task_handles = {}

    @staticmethod
    def Instance():
        """
        Get the local node instance.

        Returns:
            NodeLeader: instance.
        """
        if NodeLeader._LEAD is None:
            NodeLeader._LEAD = NodeLeader()
        return NodeLeader._LEAD

    def __init__(self):
        """
        Create an instance.
        This is the equivalent to C#'s LocalNode.cs
        """
        self.Setup()
        self.ServiceEnabled = settings.SERVICE_ENABLED
        self.peer_zero_count = 0  # track the number of times PeerCheckLoop saw a Peer count of zero. Reset e.g. after 3 times
        self.connection_queue = []

    def start_peer_check_loop(self):
        logger.debug(f"start_peer_check_loop")
        if self.peer_check_loop and self.peer_check_loop.running:
            logger.debug("start_peer_check_loop: still running -> stopping...")
            self.stop_peer_check_loop()

        self.peer_check_loop = task.LoopingCall(self.PeerCheckLoop)  # , self.MempoolCheckLoop)
        self.peer_check_loop_deferred = self.peer_check_loop.start(10, now=False)
        self.peer_check_loop_deferred.addErrback(self.OnPeerLoopError)

    def stop_peer_check_loop(self, cancel=True):
        logger.debug(f"stop_peer_check_loop, cancel: {cancel}")
        if self.peer_check_loop and self.peer_check_loop.running:
            logger.debug(f"stop_peer_check_loop, calling stop()")
            self.peer_check_loop.stop()
        if cancel and self.peer_check_loop_deferred:
            logger.debug(f"stop_peer_check_loop, calling cancel()")
            self.peer_check_loop_deferred.cancel()

    def start_check_bcr_loop(self):
        logger.debug(f"start_check_bcr_loop")
        if self.check_bcr_loop and self.check_bcr_loop.running:
            logger.debug("start_check_bcr_loop: still running -> stopping...")
            self.stop_check_bcr_loop()

        self.check_bcr_loop = task.LoopingCall(self.check_bcr_catchup)
        self.check_bcr_loop_deferred = self.check_bcr_loop.start(5)
        self.check_bcr_loop_deferred.addErrback(self.OnCheckBcrError)

    def stop_check_bcr_loop(self, cancel=True):
        logger.debug(f"stop_check_bcr_loop, cancel: {cancel}")
        if self.check_bcr_loop and self.check_bcr_loop.running:
            logger.debug(f"stop_check_bcr_loop, calling stop()")
            self.check_bcr_loop.stop()
        if cancel and self.check_bcr_loop_deferred:
            logger.debug(f"stop_check_bcr_loop, calling cancel()")
            self.check_bcr_loop_deferred.cancel()

    def start_memcheck_loop(self):
        self.stop_memcheck_loop()
        self.memcheck_loop = task.LoopingCall(self.MempoolCheck)
        self.memcheck_loop_deferred = self.memcheck_loop.start(240, now=False)
        self.memcheck_loop_deferred.addErrback(self.OnMemcheckError)

    def stop_memcheck_loop(self, cancel=True):
        if self.memcheck_loop and self.memcheck_loop.running:
            self.memcheck_loop.stop()
        if cancel and self.memcheck_loop_deferred:
            self.memcheck_loop_deferred.cancel()

    def start_blockheight_loop(self):
        self.stop_blockheight_loop()
        self.CurrentBlockheight = BC.Default().Height
        self.blockheight_loop = task.LoopingCall(self.BlockheightCheck)
        self.blockheight_loop_deferred = self.blockheight_loop.start(240, now=False)
        self.blockheight_loop_deferred.addErrback(self.OnBlockheightcheckError)

    def stop_blockheight_loop(self, cancel=True):
        if self.blockheight_loop and self.blockheight_loop.running:
            self.blockheight_loop.stop()
        if cancel and self.blockheight_loop_deferred:
            self.blockheight_loop_deferred.cancel()

    def Setup(self):
        """
        Initialize the local node.

        Returns:

        """
        self.Peers = []  # active nodes that we're connected to
        self.UnconnectedPeers = []
        self.KNOWN_ADDRS = []  # node addresses that we've learned about from other nodes
        self.DEAD_ADDRS = []  # addresses that were performing poorly or we could not establish a connection to
        self.MissionsGlobal = []
        self.NodeId = random.randint(1294967200, 4294967200)

    def Restart(self):
        self.stop_peer_check_loop()
        self.stop_check_bcr_loop()
        self.stop_memcheck_loop()
        self.stop_blockheight_loop()

        self.peer_check_loop_deferred = None
        self.check_bcr_loop_deferred = None
        self.memcheck_loop_deferred = None
        self.blockheight_loop_deferred = None

        if len(self.Peers) == 0:
            # preserve any addresses we know because the peers in the seedlist might have gone bad and then we can't receive new addresses anymore
            unique_addresses = list(set(self.KNOWN_ADDRS + self.DEAD_ADDRS))
            self.KNOWN_ADDRS = unique_addresses
            self.DEAD_ADDRS = []
            self.peer_zero_count = 0
            self.connection_queue = []

            self.Start(skip_seeds=True)

    def throttle_sync(self):
        for peer in self.Peers:  # type: NeoNode
            peer.stop_block_loop(cancel=False)
            peer.stop_peerinfo_loop(cancel=False)
            peer.stop_header_loop(cancel=False)

        # start a loop to check if we've caught up on our requests
        if not self.check_bcr_loop:
            self.start_check_bcr_loop()

    def check_bcr_catchup(self):
        """we're exceeding data request speed vs receive + process"""
        logger.debug(f"Checking if BlockRequests has caught up {len(BC.Default().BlockRequests)}")

        # test, perhaps there's some race condition between slow startup and throttle sync, otherwise blocks will never go down
        for peer in self.Peers:  # type: NeoNode
            peer.stop_block_loop(cancel=False)
            peer.stop_peerinfo_loop(cancel=False)
            peer.stop_header_loop(cancel=False)

        if len(BC.Default().BlockRequests) > 0:
            for peer in self.Peers:
                peer.health_check(HEARTBEAT_BLOCKS)
        else:
            # we're done catching up. Stop own loop and restart peers
            self.stop_check_bcr_loop()
            self.check_bcr_loop = None
            logger.debug("BlockRequests have caught up...resuming sync")
            for peer in self.Peers:
                peer.ProtocolReady()  # this starts all loops again
                # give a little bit of time between startup of peers
                time.sleep(2)

    def _process_connection_queue(self):
        start_delay = 0
        for addr in self.connection_queue:
            host, port = addr.split(":")
            setupConnDeferred = task.deferLater(reactor, start_delay, self.SetupConnection, host, port)
            setupConnDeferred.addErrback(self.OnSetupConnectionErr)
            start_delay += 1

        # self.connection_queue = []

    def Start(self, skip_seeds=False):
        """Start connecting to the node list."""
        logger.debug("Starting up nodeleader")
        start_delay = 0
        if not skip_seeds:
            logger.debug("Attempting to connect to seed list...")
            for bootstrap in settings.SEED_LIST:
                host, port = bootstrap.split(":")
                setupConnDeferred = task.deferLater(reactor, start_delay, self.SetupConnection, host, port)
                setupConnDeferred.addErrback(self.OnSetupConnectionErr)
                start_delay += 1

        logger.debug("Starting up nodeleader: starting peer, mempool, and blockheight check loops")
        # check in on peers every 10 seconds
        self.start_peer_check_loop()
        self.start_memcheck_loop()
        self.start_blockheight_loop()

        if settings.ACCEPT_INCOMING_PEERS:
            logger.debug(f"Starting up nodeleader: setting up listen server on port: '{settings.NODE_PORT}")
            reactor.listenTCP(settings.NODE_PORT, NeoClientFactory(incoming_client=True))

    def setBlockReqSizeAndMax(self, breqpart=0, breqmax=0):
        if breqpart > 0 and breqmax > 0 and breqmax > breqpart:
            self.BREQPART = breqpart
            self.BREQMAX = breqmax
            logger.info("Set each node to request %s blocks per request with a total of %s in queue" % (
                self.BREQPART, self.BREQMAX))
        else:
            logger.info(
                "invalid values. Please specify a block request part and max size for each node, like 30 and 1000")

    def setBlockReqSizeByName(self, name):
        if name.lower() == 'slow':
            self.BREQPART = 15
            self.BREQMAX = 5000
        elif name.lower() == 'normal':
            self.BREQPART = 100
            self.BREQMAX = 10000
        elif name.lower() == 'fast':
            self.BREQPART = 250
            self.BREQMAX = 15000
        else:
            logger.info("configuration name %s not found. use 'slow', 'normal', or 'fast'" % name)

        logger.info("Set each node to request %s blocks per request with a total of %s in queue" % (
            self.BREQPART, self.BREQMAX))

    def RemoteNodePeerReceived(self, host, port, via_node_addr):
        addr = Address("%s:%s" % (host, port))
        if addr not in self.KNOWN_ADDRS and addr not in self.DEAD_ADDRS:
            logger.debug(f"Adding new address {addr:>21} to known addresses list, received from {via_node_addr}")
            # we always want to save new addresses in case we lose all active connections before we can request a new list
            self.KNOWN_ADDRS.append(addr)

    def SetupConnection(self, host, port):
        if len(self.Peers) < settings.CONNECTED_PEER_MAX:
            try:
                reactor.connectTCP(host, int(port), NeoClientFactory(), timeout=120)
            except Exception as e:
                logger.error("Could not connect TCP to %s:%s " % (host, port))

    def Shutdown(self):
        """Disconnect all connected peers."""

        self.stop_peer_check_loop()
        self.peer_check_loop_deferred = None

        self.stop_check_bcr_loop()
        self.check_bcr_loop_deferred = None

        self.stop_memcheck_loop()
        self.memcheck_loop_deferred = None

        self.stop_blockheight_loop()
        self.blockheight_loop_deferred = None

        for p in self.Peers:
            p.Disconnect()

    def AddConnectedPeer(self, peer):
        """
        Add a new connect peer to the known peers list.

        Args:
            peer (NeoNode): instance.
        """
        if peer.Address in self.connection_queue:
            self.connection_queue.remove(peer.Address)

        if peer not in self.Peers and len(self.Peers) < settings.CONNECTED_PEER_MAX:
            self.Peers.append(peer)
            if peer.Address not in self.KNOWN_ADDRS:
                self.KNOWN_ADDRS.append(peer.Address)
        else:
            # either peer is already in the list and it has reconnected before it timed out on our side
            # or it's trying to connect multiple times
            # or we hit the max connected peer count
            if peer.Address in self.KNOWN_ADDRS:
                self.KNOWN_ADDRS.remove(peer.Address)
            peer.Disconnect()

    def RemoveConnectedPeer(self, peer):
        """
        Remove a connected peer from the known peers list.

        Args:
            peer (NeoNode): instance.
        """
        if peer in self.Peers:
            self.Peers.remove(peer)

    def RemoveFromQueue(self, addr):
        """
        Remove an address from the connection queue
        Args:
            addr:

        Returns:

        """
        if addr in self.connection_queue:
            self.connection_queue.remove(addr)

    def OnSetupConnectionErr(self, err):
        if type(err.value) == CancelledError:
            return
        logger.debug("On setup connection error! %s" % err)

    def OnCheckBcrError(self, err):
        if type(err.value) == CancelledError:
            return
        logger.debug("On Check BlockRequest error! %s" % err)

    def OnPeerLoopError(self, err):
        if type(err.value) == CancelledError:
            return
        logger.debug("Error on Peer check loop %s " % err)

    def OnMemcheckError(self, err):
        if type(err.value) == CancelledError:
            return
        logger.debug("Error on Memcheck check %s " % err)

    def OnBlockheightcheckError(self, err):
        if type(err.value) == CancelledError:
            return
        logger.debug("Error on Blockheight check loop %s " % err)

    def PeerCheckLoop(self):
        # often times things will get stuck on 1 peer so
        # every so often we will try to reconnect to peers
        # that were previously active but lost their connection
        logger.debug(
            f"Peer check loop...checking [A:{len(self.KNOWN_ADDRS)} D:{len(self.DEAD_ADDRS)} C:{len(self.Peers)} M:{settings.CONNECTED_PEER_MAX} Q:{len(self.connection_queue)}]")

        self._monitor_for_zero_connected_peers()

        connected = []
        peer_to_remove = []

        for peer in self.Peers:
            if peer.endpoint == "":
                peer_to_remove.append(peer)
            else:
                connected.append(peer.Address)
        for p in peer_to_remove:
            self.Peers.remove(p)

        self._ensure_peer_tasks_running(connected)
        self._check_for_queuing_possibilities(connected)
        self._process_connection_queue()

    def _check_for_queuing_possibilities(self, connected):
        # we sort addresses such that those that we recently disconnected from are last in the list
        self.KNOWN_ADDRS.sort(key=lambda address: address.last_connection)
        to_remove = []
        for addr in self.KNOWN_ADDRS:
            if addr in self.DEAD_ADDRS:
                logger.debug(f"Address {addr} found in DEAD_ADDRS list...skipping")
                to_remove.append(addr)
                continue
            if addr not in connected and addr not in self.connection_queue and len(self.Peers) + len(
                    self.connection_queue) < settings.CONNECTED_PEER_MAX:
                self.connection_queue.append(addr)
                logger.debug(
                    f"Queuing {addr:>21} for new connection [in queue: {len(self.connection_queue)} connected: {len(self.Peers)} maxpeers:{settings.CONNECTED_PEER_MAX}]")

        # we couldn't remove addresses found in the DEAD_ADDR list from ADDRS while looping over it
        # so we do it now to clean up
        for addr in to_remove:
            try:
                self.KNOWN_ADDRS.remove(addr)
            except KeyError:
                pass

    def _monitor_for_zero_connected_peers(self):
        """
        Track if we lost connection to all peers.
        Give some retries threshold to allow peers that are in the process of connecting or in the queue to be connected to run

        """
        if len(self.Peers) == 0 and len(self.connection_queue) == 0:
            if self.peer_zero_count > 2:
                logger.debug("Peer count 0 exceeded max retries threshold, restarting...")
                self.Restart()
            else:
                logger.debug(
                    f"Peer count is 0, allow for retries or queued connections to be established {self.peer_zero_count}")
                self.peer_zero_count += 1

    def _ensure_peer_tasks_running(self, connected):
        # double check that the peers that are connected are running their tasks
        # unless we're data throttling
        # there has been a case where the connection was established, but ProtocolReady() never called nor disconnected.
        if not self.check_bcr_loop:
            for peer in self.Peers:
                if not peer.has_tasks_running:
                    peer.start_all_tasks()

    def InventoryReceived(self, inventory):
        """
        Process a received inventory.

        Args:
            inventory (neo.Network.Inventory): expect a Block type.

        Returns:
            bool: True if processed and verified. False otherwise.
        """
        if inventory.Hash.ToBytes() in self._MissedBlocks:
            self._MissedBlocks.remove(inventory.Hash.ToBytes())

        if inventory is MinerTransaction:
            return False

        if type(inventory) is Block:
            if BC.Default() is None:
                return False

            if BC.Default().ContainsBlock(inventory.Index):
                return False

            if not BC.Default().AddBlock(inventory):
                return False

        else:
            if not inventory.Verify(self.MemPool.values()):
                return False

    def RelayDirectly(self, inventory):
        """
        Relay the inventory to the remote client.

        Args:
            inventory (neo.Network.Inventory):

        Returns:
            bool: True if relayed successfully. False otherwise.
        """
        relayed = False

        self.RelayCache[inventory.Hash.ToBytes()] = inventory

        for peer in self.Peers:
            relayed |= peer.Relay(inventory)

        if len(self.Peers) == 0:
            if type(BC.Default()) is TestLevelDBBlockchain:
                # mock a true result for tests
                return True

            logger.info("no connected peers")

        return relayed

    def Relay(self, inventory):
        """
        Relay the inventory to the remote client.

        Args:
            inventory (neo.Network.Inventory):

        Returns:
            bool: True if relayed successfully. False otherwise.
        """
        if type(inventory) is MinerTransaction:
            return False

        if inventory.Hash.ToBytes() in self.KnownHashes:
            return False

        self.KnownHashes.append(inventory.Hash.ToBytes())

        if type(inventory) is Block:
            pass

        elif type(inventory) is Transaction or issubclass(type(inventory), Transaction):
            if not self.AddTransaction(inventory):
                # if we fail to add the transaction for whatever reason, remove it from the known hashes list or we cannot retry the same transaction again
                try:
                    self.KnownHashes.remove(inventory.Hash.ToBytes())
                except ValueError:
                    # it not found
                    pass
                return False
        else:
            # consensus
            pass

        relayed = self.RelayDirectly(inventory)
        return relayed

    def GetTransaction(self, hash):
        if hash in self.MemPool.keys():
            return self.MemPool[hash]
        return None

    def AddTransaction(self, tx):
        """
        Add a transaction to the memory pool.

        Args:
            tx (neo.Core.TX.Transaction): instance.

        Returns:
            bool: True if successfully added. False otherwise.
        """
        if BC.Default() is None:
            return False

        if tx.Hash.ToBytes() in self.MemPool.keys():
            return False

        if BC.Default().ContainsTransaction(tx.Hash):
            return False

        if not tx.Verify(self.MemPool.values()):
            logger.error("Verifying tx result... failed")
            return False

        self.MemPool[tx.Hash.ToBytes()] = tx

        return True

    def RemoveTransaction(self, tx):
        """
        Remove a transaction from the memory pool if it is found on the blockchain.

        Args:
            tx (neo.Core.TX.Transaction): instance.

        Returns:
            bool: True if successfully removed. False otherwise.
        """
        if BC.Default() is None:
            return False

        if not BC.Default().ContainsTransaction(tx.Hash):
            return False

        if tx.Hash.ToBytes() in self.MemPool:
            del self.MemPool[tx.Hash.ToBytes()]
            return True

        return False

    def MempoolCheck(self):
        """
        Checks the Mempool and removes any tx found on the Blockchain
        Implemented to resolve https://github.com/CityOfZion/neo-python/issues/703
        """
        txs = []
        values = self.MemPool.values()
        for tx in values:
            txs.append(tx)

        for tx in txs:
            res = self.RemoveTransaction(tx)
            if res:
                logger.debug("found tx 0x%s on the blockchain ...removed from mempool" % tx.Hash)

    def BlockheightCheck(self):
        """
        Checks the current blockheight and restarts NodeLeader if not advancing
        """
        if self.CurrentBlockheight == BC.Default().Height:
            logger.debug("Blockheight is not advancing ...restarting NodeLeader")
            for peer in self.Peers:
                peer.Disconnect()
        else:
            self.CurrentBlockheight = BC.Default().Height
