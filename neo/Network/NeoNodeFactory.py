from twisted.internet.protocol import Protocol, Factory
from .NeoNode import NeoNode



from neo.Core.Block import Block
from neo.Core.Blockchain import Blockchain
from neo.Network.Message import Message
from neo.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream
from neo.IO.Helper import Helper as IOHelper
from neo.Core.Helper import Helper
from neo.Core.TX.Transaction import Transaction
from neo.Core.TX.MinerTransaction import MinerTransaction

from .Payloads.AddrPayload import AddrPayload
from .Payloads.ConsensusPayload import ConsensusPayload
from .Payloads.FilterLoadPayload import FilterLoadPayload
from .Payloads.FilterAddPayload import FilterAddPayload
from .Payloads.GetBlocksPayload import GetBlocksPayload
from .Payloads.HeadersPayload import HeadersPayload
from .Payloads.InvPayload import InvPayload
from .Payloads.MerkleBlockPayload import MerkleBlockPayload
from .Payloads.NetworkAddressWithTime import NetworkAddressWithTime
from .Payloads.VersionPayload import VersionPayload
from .InventoryType import InventoryType
from autologging import logged

@logged
class NeoFactory(Factory):

    peers = []
    nodeid = 12234234
    blockchain = None

    blockrequests = []

    def __init__(self):
        self.startFactory()

    def startFactory(self):
        self.peers = []
        self.nodeid = 1123123
        self.blockchain = Blockchain.Default()
        self.blockchain.SyncReset.on_change += self.LevelDB_onreset

    def stopFactory(self):
        print("stopping factory")
        self.blockchain.SyncReset.on_change -= self.LevelDB_onreset
        self.blockchain = None


    def buildProtocol(self, addr):
        return NeoNode(self)



    def InventoryReceived(self, inventory):

        self.__log.debug("Neo factory received inventory %s " % inventory)

        if inventory is MinerTransaction: return False

        #lock known hashes
#        if inventory.Hash() in self._known_hashes: return False
        #endlock

        if type(inventory) is Block:
            if Blockchain.Default() == None: return False

            if Blockchain.Default().ContainsBlock(inventory.HashToByteString()):
                self.__log.debug("cant add block %s because blockchain already contains it " % inventory.HashToByteString())
                return False
            self.__log.debug("Will Try to add block" % inventory.HashToByteString())

            if not Blockchain.Default().AddBlock(inventory): return False

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


    def LevelDB_onreset(self, hash):
        self.__log.debug("Recevied leveldb reset function %s " % hash)
        self.blockrequests = []
        for peer in self.peers:
            print("peer is %s " % peer)
            peer.HandleBlockReset(hash)