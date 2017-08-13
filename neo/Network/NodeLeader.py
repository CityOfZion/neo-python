
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

    UnconnectedPeers = []

    NodeId = None

    _RunLoop = None

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
        self.NodeId = random.randint(1294967200,4294967200)
        self._RunLoop = task.LoopingCall(self.RunLoop)

    def Start(self):
        # start up endpoints
        for bootstrap in Settings.SEED_LIST:
            host, port = bootstrap.split(":")
            point = TCP4ClientEndpoint(reactor, host, int(port))
            d = connectProtocol(point, NeoNode(NeoFactory, self))

            d.addCallbacks(self.onProtocolConnected, self.onProtocolError)

        self._RunLoop.start(10)

    def Shutdown(self):
        print("shut down!")
        self._RunLoop.stop()

        for p in self.Peers:
            p.transport.loseConnection()

    def onProtocolConnected(self, peer):
        self.__log.debug("PRotocol connected!! %s " % peer)
        if not peer in self.Peers:
            self.Peers.append(peer)

        if peer in self.UnconnectedPeers:
            self.UnconnectedPeers.remove(peer)

    def onProtocolError(self, reason):
        self.__log.debug("Protocol exception %s " % vars(reason))



    #    @profile()
    def InventoryReceived(self, inventory):

        self.__log.debug("Node Leader received inventory %s " % inventory)

        if inventory is MinerTransaction: return False

        # lock known hashes
        #        if inventory.Hash() in self._known_hashes: return False
        # endlock

        if type(inventory) is Block:
            if BC.Default() == None: return False

            if BC.Default().ContainsBlock(inventory.Index):
                #                self.__log.debug("cant add block %s because blockchain already contains it " % inventory.HashToByteString())
                return False
                #            self.__log.debug("Will Try to add block" % inventory.HashToByteString())

            if not BC.Default().AddBlock(inventory): return False

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


    def RunLoop(self):
        self.__log.debug("tick P:%s U:%s" % (len(self.Peers), len(self.UnconnectedPeers)))

        if len(self.Peers) > 0:

            peer = random.choice(self.Peers)
            self.__log.debug("Asking Peer %s to send peer info " % peer)
            peer.SendPeerInfo()
#        self.__log.debug("Doing Unconnected %s" % self.UnconnectedPeers)