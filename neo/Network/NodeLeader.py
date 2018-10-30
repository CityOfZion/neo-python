import random
from neo.Core.Block import Block
from neo.Core.Blockchain import Blockchain as BC
from neo.Implementations.Blockchains.LevelDB.TestLevelDBBlockchain import TestLevelDBBlockchain
from neo.Core.TX.Transaction import Transaction
from neo.Core.TX.MinerTransaction import MinerTransaction
from neo.Network.NeoNode import NeoNode
from neo.Settings import settings
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor, task
from neo.logging import log_manager

logger = log_manager.getLogger('network')


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
        address = "%s:%s" % (connector.host, connector.port)
        logger.debug("Failed connecting to %s " % address)
        if "Connection refused" in str(reason) or "Operation timed out" in str(reason):
            if address in NodeLeader.Instance().ADDRS:
                NodeLeader.Instance().ADDRS.remove(address)
                if address not in NodeLeader.Instance().DEAD_ADDRS:
                    NodeLeader.Instance().DEAD_ADDRS.append(address)

    def clientConnectionLost(self, connector, reason):
        address = "%s:%s" % (connector.host, connector.port)
        logger.debug("Dropped connection from %s " % address)
        for peer in NodeLeader.Instance().Peers:
            if peer.Address == address:
                peer.connectionLost()


class NodeLeader:
    _LEAD = None

    Peers = []

    UnconnectedPeers = []

    ADDRS = []
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

    ServiceEnabled = False

    peer_loop_deferred = None

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

    def Setup(self):
        """
        Initialize the local node.

        Returns:

        """
        self.Peers = []
        self.UnconnectedPeers = []
        self.ADDRS = []
        self.DEAD_ADDRS = []
        self.MissionsGlobal = []
        self.NodeId = random.randint(1294967200, 4294967200)

    def Restart(self):
        if self.peer_loop_deferred:
            self.peer_loop_deferred.cancel()
            self.peer_loop_deferred = None

        if len(self.Peers) == 0:
            self.ADDRS = []
            self.DEAD_ADDRS = []
            self.Start()

    def Start(self):
        """Start connecting to the node list."""
        start_delay = 0
        for bootstrap in settings.SEED_LIST:
            host, port = bootstrap.split(":")
            setupConnDeferred = task.deferLater(reactor, start_delay, self.SetupConnection, host, port)
            setupConnDeferred.addErrback(self.onSetupConnectionErr)
            start_delay += 1

        # check in on peers every 4 mins
        peer_check_loop = task.LoopingCall(self.PeerCheckLoop)
        self.peer_loop_deferred = peer_check_loop.start(240, now=False)
        self.peer_loop_deferred.addErrback(self.OnPeerLoopError)

        if settings.ACCEPT_INCOMING_PEERS:
            reactor.listenTCP(settings.NODE_PORT, NeoClientFactory(incoming_client=True))

    def setBlockReqSizeAndMax(self, breqpart=0, breqmax=0):
        if breqpart > 0 and breqmax > 0 and breqmax > breqpart:
            self.BREQPART = breqpart
            self.BREQMAX = breqmax
            logger.info("Set each node to request %s blocks per request with a total of %s in queue" % (self.BREQPART, self.BREQMAX))
        else:
            logger.info("invalid values. Please specify a block request part and max size for each node, like 30 and 1000")

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

        logger.info("Set each node to request %s blocks per request with a total of %s in queue" % (self.BREQPART, self.BREQMAX))

    def RemoteNodePeerReceived(self, host, port, index):
        addr = '%s:%s' % (host, port)
        if addr not in self.ADDRS and len(self.Peers) < settings.CONNECTED_PEER_MAX and addr not in self.DEAD_ADDRS:
            self.ADDRS.append(addr)
            setupConnDeferred = task.deferLater(reactor, index * 10, self.SetupConnection, host, port)
            setupConnDeferred.addErrback(self.onSetupConnectionErr)

    def SetupConnection(self, host, port):
        if len(self.Peers) < settings.CONNECTED_PEER_MAX:
            try:
                reactor.connectTCP(host, int(port), NeoClientFactory(), timeout=120)
            except Exception as e:
                logger.error("Could not connect TCP to %s:%s " % (host, port))

    def Shutdown(self):
        """Disconnect all connected peers."""
        if self.peer_loop_deferred:
            self.peer_loop_deferred.cancel()
            self.peer_loop_deferred = None

        for p in self.Peers:
            p.Disconnect()

    def OnPeerLoopError(self, err):
        logger.debug("Error on Peer check loop %s " % err)

    def AddConnectedPeer(self, peer):
        """
        Add a new connect peer to the known peers list.

        Args:
            peer (NeoNode): instance.
        """

        if peer not in self.Peers:

            if len(self.Peers) < settings.CONNECTED_PEER_MAX:
                self.Peers.append(peer)
                if peer.Address not in self.ADDRS:
                    self.ADDRS.append(peer.Address)
            else:
                if peer.Address in self.ADDRS:
                    self.ADDRS.remove(peer.Address)
                peer.Disconnect()

    def RemoveConnectedPeer(self, peer):
        """
        Remove a connected peer from the known peers list.

        Args:
            peer (NeoNode): instance.
        """
        if peer in self.Peers:
            self.Peers.remove(peer)

    def onSetupConnectionErr(self, err):
        logger.debug("On setup connection error! %s" % err)

    def PeerCheckLoop(self):
        # often times things will get stuck on 1 peer so
        # every so often we will try to reconnect to peers
        # that were previously active but lost their connection

        start_delay = 0
        connected = []
        for peer in self.Peers:
            connected.append(peer.Address)
        for addr in self.ADDRS:
            if addr not in connected and len(self.Peers) < settings.CONNECTED_PEER_MAX and addr not in self.DEAD_ADDRS:
                host, port = addr.split(":")
                setupConnDeferred = task.deferLater(reactor, start_delay, self.SetupConnection, host, port)
                setupConnDeferred.addErrback(self.onSetupConnectionErr)

                start_delay += 1

    def ResetBlockRequestsAndCache(self):
        """Reset the block request counter and its cache."""
        logger.debug("Resetting Block requests")
        self.MissionsGlobal = []
        BC.Default().BlockSearchTries = 0
        for p in self.Peers:
            p.myblockrequests = set()
        BC.Default().ResetBlockRequests()
        BC.Default()._block_cache = {}

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
            logger.error("Veryfiying tx result... failed")
            return False

        self.MemPool[tx.Hash.ToBytes()] = tx

        return True
