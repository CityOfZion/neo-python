import random
from logzero import logger
from neo.Core.Block import Block
from neo.Core.Blockchain import Blockchain as BC
from neo.Implementations.Blockchains.LevelDB.TestLevelDBBlockchain import TestLevelDBBlockchain
from neo.Core.TX.Transaction import Transaction
from neo.Core.TX.MinerTransaction import MinerTransaction
from neo.Network.NeoNode import NeoNode
from neo.Settings import settings
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.internet import reactor


class NeoClientFactory(ReconnectingClientFactory):
    protocol = NeoNode
    maxRetries = 1

    def clientConnectionFailed(self, connector, reason):
        address = "%s:%s" % (connector.host, connector.port)
        logger.debug("Dropped connection from %s " % address)
        for peer in NodeLeader.Instance().Peers:
            if peer.Address == address:
                peer.connectionLost()


class NodeLeader:
    __LEAD = None

    Peers = []

    UnconnectedPeers = []

    ADDRS = []

    NodeId = None

    _MissedBlocks = []

    BREQPART = 100
    NREQMAX = 500
    BREQMAX = 10000

    KnownHashes = []
    MissionsGlobal = []
    MemPool = {}
    RelayCache = {}

    NodeCount = 0

    ServiceEnabled = False

    @staticmethod
    def Instance():
        """
        Get the local node instance.

        Returns:
            NodeLeader: instance.
        """
        if NodeLeader.__LEAD is None:
            NodeLeader.__LEAD = NodeLeader()
        return NodeLeader.__LEAD

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
        self.MissionsGlobal = []
        self.NodeId = random.randint(1294967200, 4294967200)

    def Restart(self):
        if len(self.Peers) == 0:
            self.ADDRS = []
            self.Start()

    def Start(self):
        """Start connecting to the node list."""
        # start up endpoints
        start_delay = 0
        for bootstrap in settings.SEED_LIST:
            host, port = bootstrap.split(":")
            self.ADDRS.append('%s:%s' % (host, port))
            reactor.callLater(start_delay, self.SetupConnection, host, port)
            start_delay += 1

    def RemoteNodePeerReceived(self, host, port, index):
        addr = '%s:%s' % (host, port)
        if addr not in self.ADDRS and len(self.Peers) < settings.CONNECTED_PEER_MAX:
            self.ADDRS.append(addr)
            reactor.callLater(index * 10, self.SetupConnection, host, port)

    def SetupConnection(self, host, port):
        if len(self.Peers) < settings.CONNECTED_PEER_MAX:
            reactor.connectTCP(host, int(port), NeoClientFactory())

    def Shutdown(self):
        """Disconnect all connected peers."""
        for p in self.Peers:
            p.Disconnect()

    def AddConnectedPeer(self, peer):
        """
        Add a new connect peer to the known peers list.

        Args:
            peer (NeoNode): instance.
        """

        if peer not in self.Peers:

            if len(self.Peers) < settings.CONNECTED_PEER_MAX:
                self.Peers.append(peer)
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
        if peer.Address in self.ADDRS:
            self.ADDRS.remove(peer.Address)
        if len(self.Peers) == 1:
            self.Peers[0].Disconnect()
        elif len(self.Peers) == 0:
            reactor.callLater(10, self.Restart)

    def ResetBlockRequestsAndCache(self):
        """Reset the block request counter and its cache."""
        logger.debug("Resseting Block requests")
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
        # self.
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
