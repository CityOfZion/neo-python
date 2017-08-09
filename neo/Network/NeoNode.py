from twisted.internet.endpoints import TCP4ClientEndpoint,TCP4ServerEndpoint
from twisted.internet.interfaces import IPullProducer,IPushProducer
from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
import json
import time
import binascii
from autologging import logged


from neo.Core.Block import Block
from neo.Core.Blockchain import Blockchain
from neo.Network.Message import Message,ChecksumException
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
import random

from neo import Settings

@logged
class NeoNode(Protocol):

    Version = None



    def __init__(self, factory):
        self.factory = factory
        self.nodeid = self.factory.nodeid
        self.state = "HELLO"
        self.remote_nodeid = random.randint(1294967200,4294967200)
        self.endpoint = ''
        self.blockchain = None
        self.buffer_in = bytearray()
        self.pm = None
        self.reset_counter = False
        self.myblockrequests=[]
        self.bytes_in = 0
        self.bytes_out = 0



    def Disconnect(self):
        self.transport.loseConnection()
        self.state = 'DISCONNECT'

    def Name(self):
        return self.transport.getPeer()

    def IOStats(self):
        biM = self.bytes_in / 1000000 #megabyes
        boM = self.bytes_out / 1000000

        return "%s MB in / %s MB out" % (biM, boM)

    def connectionMade(self):
        self.state = "CONNECTING"
        self.blockchain = Blockchain.Default()
        self.endpoint = self.transport.getPeer()
        self.factory.peers.append(self)
        self.Log("Connection from %s" % self.endpoint)


    def connectionLost(self, reason=None):
        self.state = "HELLO"
        self.blockchain = None
        self.buffer_in = None
        self.pm = None

        if self in self.factory.peers:
            self.factory.peers.remove(self)

        for h in self.myblockrequests:
            if h in self.factory.blockrequests:
                self.factory.blockrequests.remove(h)

        self.myblockrequests = None


        self.Log("%s disconnected" % self.nodeid, )



    def dataReceived(self, data):

        self.bytes_in += (len(data))

        self.buffer_in = self.buffer_in + data

        self.CheckDataReceived()


    def CheckDataReceived(self):

        if len(self.buffer_in) >= 24:

            mstart = self.buffer_in[:24]
            ms = MemoryStream(mstart)
            reader = BinaryReader(ms)


            try:
                m = Message()
                m.Magic =reader.ReadUInt32()
                m.Command = reader.ReadFixedString(12).decode('utf-8')
                m.Length = reader.ReadUInt32()
                m.Checksum = reader.ReadUInt32()
                self.pm = m
                del ms
                del reader
            except Exception as e:
                self.Log('could not read initial bytes %s ' % e)

            self.CheckMessageData()

    def CheckMessageData(self):
        if not self.pm: return

        currentlength = len(self.buffer_in)
        messageExpectedLength = 24 + self.pm.Length
        #percentcomplete = int(100 * (currentlength / messageExpectedLength))
        #self.Log("Receiving %s data: %s percent complete" % (self.pm.Command, percentcomplete))

        if currentlength >= messageExpectedLength:
            mdata = self.buffer_in[:messageExpectedLength]
            stream = MemoryStream(mdata)
            reader = BinaryReader(stream)
            message = Message()
            message.Deserialize(reader)

            self.buffer_in = self.buffer_in[messageExpectedLength:]
            self.pm = None
            self.MessageReceived(message)
            self.reset_counter = False
            del mdata
            del stream
            del reader
            while len(self.buffer_in) >=24 and not self.reset_counter:
                self.CheckDataReceived()

        else:
            self.reset_counter = True

    def MessageReceived(self, m):

        self.Log("Messagereceived and processed ...: %s " % m.Command)

        if m.Command == 'verack':
            self.HandleVerack()
        elif m.Command == 'version':
            self.HandleVersion(m.Payload)
        elif m.Command == 'getaddr':
            self.HandleGetAddress(m.Payload)
        elif m.Command == 'inv':
            self.HandleInvMessage(m.Payload)
        elif m.Command == 'block':
            self.HandleBlockReceived(m.Payload)
        elif m.Command == 'headers':
            self.HandleBlockHeadersReceived(m.Payload)

        else:
            self.Log("Command %s not implemented " % m.Command)


    def ProtocolReady(self):
        self.AskForMoreHeaders()
        self.AskForMoreBlocks()

    def AskForMoreHeaders(self):
        self.Log("asking for more headers...")
        get_headers_message = Message("getheaders", GetBlocksPayload(self.blockchain.CurrentHeaderHash()))
        self.SendSerializedMessage(get_headers_message)

    def AskForMoreBlocks(self):
        self.Log("asking for more blocks ...")
        get_blocks_message =  Message("getblocks", GetBlocksPayload(self.blockchain.CurrentBlockHashPlusOne()))
        self.SendSerializedMessage(get_blocks_message)


    def SendVersion(self):
        m = Message("version", VersionPayload(Settings.NODE_PORT, self.nodeid, Settings.VERSION_NAME))
        self.SendSerializedMessage(m)


    def HandleVersion(self, payload):
        self.Version = IOHelper.AsSerializableWithType(payload, "neo.Network.Payloads.VersionPayload.VersionPayload")
        self.remote_nodeid = self.Version.Nonce
        self.state = 'ESTABLISHED'
        self.SendVersion()

    def HandleGetAddress(self, payload):
        self.Log("not handling addresses right now")
        return

    def HandleVerack(self):
        m = Message('verack')
        self.SendSerializedMessage(m)
        self.ProtocolReady()

    def HandleInvMessage(self, payload):
        inventory = IOHelper.AsSerializableWithType(payload, 'neo.Network.Payloads.InvPayload.InvPayload')

        if inventory.Type == int.from_bytes(InventoryType.Consensus, 'little'):
            self.HandleConsenusInventory(inventory)
        elif inventory.Type == int.from_bytes(InventoryType.TX, 'little'):
            self.HandleTransactionInventory(inventory)
        elif inventory.Type == int.from_bytes(InventoryType.Block, 'little'):
            self.HandleBlockHashInventory(inventory)



    def SendSerializedMessage(self, message):
        ba = Helper.ToArray(message)
        ba2 = binascii.unhexlify(ba)
        self.transport.write(ba2)
        self.bytes_out += len(ba2)
        del ba
        del ba2


    def HandleConsenusInventory(self, inventory):
        self.Log("handle consensus not implemented")


    def HandleTransactionInventory(self, inventory):
        self.Log("handle transaction not implemented")


    def HandleBlockHashInventory(self, inventory=None):

        if Blockchain.Default().BlockCacheCount() > 3000:

            self.__log.debug("************************************************")
            self.__log.debug("BLOCK CACHE COUNT TOO HIGH, PAUSE FOR NOW")
            self.__log.debug("********************************************")

            reactor.callLater(5, self.HandleBlockHashInventory, inventory)
            return

        hashes = []
        hashstart = self.blockchain.Height() + 1
        while hashstart < self.blockchain.HeaderHeight() and len(hashes) < 200:
            hash = self.blockchain.GetHeaderHash(hashstart)
            if not hash in self.factory.blockrequests and not hash in self.myblockrequests:
                self.factory.blockrequests.append(hash)
                self.myblockrequests.append(hash)
                hashes.append(hash)
            hashstart += 1

        if len(hashes) == 0:

            self.Log("ALL BLOCKS COMPLETE.... Wait for more headers")
            self.AskForMoreHeaders()

        else:
            self.Log("requesting %s hashes  " % len(hashes))


            message = Message("getdata", InvPayload(InventoryType.Block, hashes))
            self.SendSerializedMessage(message)



    def HandleBlockHeadersReceived(self, inventory):
        inventory = IOHelper.AsSerializableWithType(inventory, 'neo.Network.Payloads.HeadersPayload.HeadersPayload')

        self.blockchain.AddHeaders(inventory.Headers)
        del inventory
        if self.blockchain.HeaderHeight() < self.Version.StartHeight:
            self.AskForMoreHeaders()

    def HandleBlockReceived(self, inventory):

        block = IOHelper.AsSerializableWithType(inventory, 'neo.Core.Block.Block')

        #self.Log("ON BLOCK INVENTORY RECEIVED........... %s " % block.Index)

        blockhash =  block.HashToString()

        if blockhash in self.factory.blockrequests:
            self.factory.blockrequests.remove(blockhash)
        if blockhash in self.myblockrequests:
            self.myblockrequests.remove(blockhash)

        self.factory.InventoryReceived(self.factory,block)


    def HandleBlockReset(self, hash):
        self.myblockrequests = []

    def Log(self, message):
        self.__log.debug("%s - %s" % (self.endpoint, message))