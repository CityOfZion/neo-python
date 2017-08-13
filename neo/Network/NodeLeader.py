
from neo.Core.Block import Block
from neo.Core.Blockchain import Blockchain as BC
from neo.Core.TX.Transaction import Transaction
from neo.Core.TX.MinerTransaction import MinerTransaction
from neo.Network.NeoNode import NeoNode
from neo.Network.NeoNodeFactory import NeoFactory
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
    BREQMAX= 3000

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
        BC.Default().MissingBlock.on_change += self.OnMissingBlockEvent

    def Start(self):
        # start up endpoints
        for bootstrap in Settings.SEED_LIST:
            host, port = bootstrap.split(":")
            self.ADDRS.append('%s:%s' % (host,port))
            self.SetupConnection(host, port)


    def RemoteNodePeerReceived(self, host, port):
        addr = '%s:%s' % (host,port)
        if not addr in self.ADDRS:
            if len(self.Peers) < self.ConnectedPeersMax:
                self.ADDRS.append(addr)
                self.SetupConnection(host, port)

    def SetupConnection(self, host, port):
        self.__log.debug("Setting up connection! %s %s " % (host, port))
        point = TCP4ClientEndpoint(reactor, host, int(port))
        d = connectProtocol(point, NeoNode(NeoFactory, self))
        d.addCallbacks(self.onProtocolConnected, self.onProtocolError)
        reactor.callLater(2, d.cancel)

    def Shutdown(self):
        print("shut down!")
#        self._RunLoop.stop()

        for p in self.Peers:
            p.Disconnect()

    def onProtocolConnected(self, peer):
        self.__log.debug("PRotocol connected!! %s " % peer)
        if not peer in self.Peers:
            self.Peers.append(peer)

        if peer in self.UnconnectedPeers:
            self.UnconnectedPeers.remove(peer)

    def onProtocolError(self, reason):
        self.__log.debug("Protocol exception %s " % vars(reason))


    def OnMissingBlockEvent(self, hash):
        if not hash in self._MissedBlocks:
            self.__log.debug("ON MISSING BLOCK!!!!!!!!!!!!!")
            if hash in BC.Default().BlockRequests():
                self.__log.debug("hash was in block requests")
            else:
                self.__log.debug("HASH WASNT IN BLOCK REQUESTSSS!!!!")
            self._MissedBlocks.append(hash)
#            header = BC.Default().GetHeader(hash)
#            for index,peer in enumerate(self.Peers):
#                hash_to_get = BC.Default().GetHeaderHash(header.Index + index)
            p = random.choice(self.Peers)
            p.RequestMissigBlock(hash)
            p = random.choice(self.Peers)
            p.RequestMissigBlock(hash)
            p = random.choice(self.Peers)
            p.RequestMissigBlock(hash)
            p = random.choice(self.Peers)
            p.RequestMissigBlock(hash)

    #    @profile()
    def InventoryReceived(self, inventory):

#        self.__log.debug("Node Leader received inventory %s " % inventory)

        if inventory.HashToByteString() in self._MissedBlocks:
            self._MissedBlocks.remove(inventory.HashToByteString())

        if inventory is MinerTransaction: return False

        # lock known hashes
        #        if inventory.Hash() in self._known_hashes: return False
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

