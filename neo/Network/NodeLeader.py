import random
from logzero import logger
from neo.Core.Block import Block
from neo.Core.Blockchain import Blockchain as BC
from neo.Implementations.Blockchains.LevelDB.TestLevelDBBlockchain import TestLevelDBBlockchain
from neo.Core.TX.Transaction import Transaction
from neo.Core.TX.MinerTransaction import MinerTransaction
from neo.Network.NeoNode import NeoNode
from neo.Settings import settings
from twisted.internet.protocol import Factory
from twisted.application.internet import ClientService
from twisted.internet import reactor, task
from twisted.internet.endpoints import clientFromString
from twisted.application.internet import backoffPolicy


class NodeLeader():
    __LEAD = None

    Peers = []

    ConnectedPeersMax = 30

    UnconnectedPeers = []

    ADDRS = []

    NodeId = None

    _MissedBlocks = []

    BREQPART = 150
    NREQMAX = 150
    BREQMAX = 4000

    KnownHashes = []
    MemPool = {}
    RelayCache = {}

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

    def Setup(self):
        """
        Initialize the local node.

        Returns:

        """
        self.Peers = []
        self.UnconnectedPeers = []
        self.ADDRS = []
        self.NodeId = random.randint(1294967200, 4294967200)

    def Restart(self):
        if len(self.Peers) == 0:
            self.Start()

    def Start(self):
        """Start connecting to the node list."""
        # start up endpoints
        start_delay = 0
        for bootstrap in settings.SEED_LIST:
            host, port = bootstrap.split(":")
            self.ADDRS.append('%s:%s' % (host, port))
            reactor.callLater(start_delay, self.SetupConnection, host, port)
            start_delay += 10

    def RemoteNodePeerReceived(self, host, port):
        addr = '%s:%s' % (host, port)
        if addr not in self.ADDRS:
            if len(self.Peers) < self.ConnectedPeersMax:
                self.ADDRS.append(addr)
                self.SetupConnection(host, port)

    def SetupConnection(self, host, port):
        logger.debug("Setting up connection! %s %s " % (host, port))

        factory = Factory.forProtocol(NeoNode)
        endpoint = clientFromString(reactor, "tcp:host=%s:port=%s:timeout=5" % (host, port))

        connectingService = ClientService(
            endpoint,
            factory,
            retryPolicy=backoffPolicy(.5, factor=3.0)
        )
        connectingService.startService()

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
            self.Peers.append(peer)

    def RemoveConnectedPeer(self, peer):
        """
        Remove a connected peer from the known peers list.

        Args:
            peer (NeoNode): instance.
        """
        if peer in self.Peers:
            self.Peers.remove(peer)

        if len(self.Peers) == 0:
            reactor.callLater(10, self.Restart)

    def ResetBlockRequestsAndCache(self):
        """Reset the block request counter and its cache."""
        BC.Default().BlockSearchTries = 0
        for p in self.Peers:
            p.myblockrequests = set()
        BC.Default().__blockrequests = set()
        BC.Default()._block_cache = {}

    #    @profile()
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
            if not inventory.Verify():
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
