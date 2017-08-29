
from neo.Core.Block import Block
from neo.Core.Blockchain import Blockchain as BC
from neo.Core.TX.Transaction import Transaction
from neo.Core.TX.MinerTransaction import MinerTransaction
from neo.Network.NeoFactory import NeoFactory
from neo.Network.NeoNode import NeoNode
from neo import Settings


from autologging import logged
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
from twisted.internet import reactor,task
import random

@logged
class NodeLeader():
    __LEAD = None

    Peers = []

    ConnectedPeersMax = 30

    UnconnectedPeers = []

    ADDRS = []

    NodeId = None

    _MissedBlocks=[]


    BREQPART=100
    NREQMAX =1000
    BREQMAX= 4000


    @staticmethod
    def Instance():
        if NodeLeader.__LEAD is None:
            NodeLeader.__LEAD = NodeLeader()
        return NodeLeader.__LEAD

    def __init__(self):
        self.Setup()

    def Setup(self):
        self.Peers = []
        self.UnconnectedPeers = []
        self.ADDRS = []
        self.NodeId = random.randint(1294967200,4294967200)

    def Start(self):
        # start up endpoints
        start_delay=0
        for bootstrap in Settings.SEED_LIST:
            host, port = bootstrap.split(":")
            self.ADDRS.append('%s:%s' % (host,port))
            reactor.callLater( start_delay, self.SetupConnection,host, port)
            start_delay+=2

    def RemoteNodePeerReceived(self, host, port):
        addr = '%s:%s' % (host,port)
        if not addr in self.ADDRS:
            if len(self.Peers) < self.ConnectedPeersMax:
                self.ADDRS.append(addr)
                self.SetupConnection(host, port)

    def SetupConnection(self, host, port):
        self.__log.debug("Setting up connection! %s %s " % (host, port))
        reactor.connectTCP(host, int(port), NeoFactory())

    def Shutdown(self):
        for p in self.Peers:
            p.Disconnect()


    #    @profile()
    def InventoryReceived(self, inventory):


        if inventory.Hash.ToBytes() in self._MissedBlocks:
            self._MissedBlocks.remove(inventory.Hash.ToBytes())

        if inventory is MinerTransaction: return False

        # lock known hashes
        #        if inventory.Hash in self._known_hashes: return False
        # endlock

        if type(inventory) is Block:
            if BC.Default() == None: return False

            if BC.Default().ContainsBlock(inventory.Index):
                return False

            if not BC.Default().AddBlock(inventory):
                return False


        elif type(inventory) is Transaction or issubclass(type(inventory), Transaction):
            if not self.AddTransaction(inventory): return False

        else:
            if not inventory.Verify(): return False


#        relayed = self.RelayDirectly(inventory)

#        return relayed


    def RelayDirectly(self, inventory):

        relayed = False
        # lock connected peers

        # RelayCache.add(inventory)

        #        for node in self._connected_peers:
        #            self.__log.debug("Relaying to remote node %s " % node)
        #            relayed |= node.Relay(inventory)

        # end lock
        return relayed

