from twisted.internet.protocol import Protocol, Factory
from .NeoNode import NeoNode



from neo.Core.Block import Block
from neo.Core.Blockchain import Blockchain as BC
from neo.Core.TX.Transaction import Transaction
from neo.Core.TX.MinerTransaction import MinerTransaction


from autologging import logged

@logged
class NeoFactory(Factory):

    peers = []
    nodeid = 12234234


    def __init__(self):
        self.startFactory()

    def startFactory(self):
        self.peers = []
        self.nodeid = 1123123

    def stopFactory(self):
        pass

    def buildProtocol(self, addr):
        return NeoNode(self)


#    @profile()
    def InventoryReceived(self, inventory):

#        self.__log.debug("Neo factory received inventory %s " % inventory)

        if inventory is MinerTransaction: return False

        #lock known hashes
#        if inventory.Hash() in self._known_hashes: return False
        #endlock

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
        #lock connected peers

        #RelayCache.add(inventory)

#        for node in self._connected_peers:
#            self.__log.debug("Relaying to remote node %s " % node)
#            relayed |= node.Relay(inventory)

        #end lock
        return relayed
