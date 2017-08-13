from twisted.internet.endpoints import TCP4ClientEndpoint,TCP4ServerEndpoint
from twisted.internet.interfaces import IPullProducer,IPushProducer
from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor,task
import json
import time
import binascii
from autologging import logged

import pprint
from neo.Core.Block import Block
from neo.Core.Blockchain import Blockchain as BC
from neo.Network.Message import Message,ChecksumException
from neo.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream,StreamManager
from neo.IO.Helper import Helper as IOHelper
from neo.Core.Helper import Helper
from neo.Core.TX.Transaction import Transaction
from neo.Core.TX.MinerTransaction import MinerTransaction

from .Payloads.AddrPayload import AddrPayload
from .Payloads.ConsensusPayload import ConsensusPayload
from .Payloads.FilterLoadPayload import FilterLoadPayload
from .Payloads.FilterAddPayload import FilterAddPayload
from .Payloads.GetBlocksPayload import GetBlocksPayload
from .Payloads.NetworkAddressWithTime import NetworkAddressWithTime
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

    leader = None

    def __init__(self, factory, leader):
        self.factory = factory
        self.leader = leader
        self.nodeid = self.leader.NodeId
        self.remote_nodeid = random.randint(1294967200,4294967200)
        self.endpoint = ''
        self.buffer_in = bytearray()
        self.pm = None
        self.reset_counter = False
        self.myblockrequests=[]
        self.bytes_in = 0
        self.bytes_out = 0

        self.host = None
        self.port = None


        self.Log("CREATED NEO NODE!!!!!!!!!")

        self.leader.UnconnectedPeers.append(self)


    def Disconnect(self):
        self.transport.loseConnection()

    def Name(self):
        return self.transport.getPeer()

    def GetNetworkAddressWithTime(self):
        if self.port is not None and self.host is not None:
            return NetworkAddressWithTime(self.host, self.port, self.Version.Services)
        return None

    def IOStats(self):
        biM = self.bytes_in / 1000000 #megabyes
        boM = self.bytes_out / 1000000

        return "%s MB in / %s MB out" % (biM, boM)

    def connectionMade(self):
        self.endpoint = self.transport.getPeer()
        self.host = self.endpoint.host
        self.port = int(self.endpoint.port)
        if not self in self.leader.Peers:
            self.leader.Peers.append(self)
        if self in self.leader.UnconnectedPeers:
            self.leader.UnconnectedPeers.remove(self)

        self.Log("Connection from %s" % self.endpoint)


    def connectionLost(self, reason=None):
        self.buffer_in = None
        self.pm = None

        if self in self.leader.Peers:
            self.leader.Peers.remove(self)

        if not self in self.leader.UnconnectedPeers:
            self.leader.UnconnectedPeers.append(self)

        for h in self.myblockrequests:
            if h in BC.Default().BlockRequests():
                BC.Default().BlockRequests().remove(h)

        self.myblockrequests = None

        self.Log("%s disconnected %s" % (self.remote_nodeid, reason))



    def dataReceived(self, data):

        self.bytes_in += (len(data))

        self.buffer_in = self.buffer_in + data

        self.CheckDataReceived()

#    @profile
    def CheckDataReceived(self):

        if len(self.buffer_in) >= 24:

            mstart = self.buffer_in[:24]
            ms = StreamManager.GetStream(mstart)
            reader = BinaryReader(ms)


            try:
                m = Message()
                m.Magic =reader.ReadUInt32()
                m.Command = reader.ReadFixedString(12).decode('utf-8')
                m.Length = reader.ReadUInt32()
                m.Checksum = reader.ReadUInt32()
                self.pm = m
            except Exception as e:
                self.Log('could not read initial bytes %s ' % e)
            finally:
                StreamManager.ReleaseStream(ms)
                del reader

            try:
                self.CheckMessageData()
            except RecursionError:
                self.Log("Recursion error!!!")
                self.Disconnect()
#    @profile
    def CheckMessageData(self):
        if not self.pm: return

        currentlength = len(self.buffer_in)
        messageExpectedLength = 24 + self.pm.Length
        #percentcomplete = int(100 * (currentlength / messageExpectedLength))
        #self.Log("Receiving %s data: %s percent complete" % (self.pm.Command, percentcomplete))

        if currentlength >= messageExpectedLength:
            mdata = self.buffer_in[:messageExpectedLength]
            stream = StreamManager.GetStream(mdata)
            reader = BinaryReader(stream)
            message = Message()
            message.Deserialize(reader)
            StreamManager.ReleaseStream(stream)
            self.buffer_in = self.buffer_in[messageExpectedLength:]
            self.pm = None
            self.MessageReceived(message)
            self.reset_counter = False
            while len(self.buffer_in) >=24 and not self.reset_counter:
                self.CheckDataReceived()

        else:
            self.reset_counter = True

    def MessageReceived(self, m):

#        self.Log("Messagereceived and processed ...: %s " % m.Command)

        if m.Command == 'verack':
            self.HandleVerack()
        elif m.Command == 'version':
            self.HandleVersion(m.Payload)
        elif m.Command == 'getaddr':
            self.SendPeerInfo()
        elif m.Command == 'inv':
            self.HandleInvMessage(m.Payload)
        elif m.Command == 'block':
#            reactor.callFromThread(self.HandleBlockReceived, m.Payload)
            self.HandleBlockReceived(m.Payload)
        elif m.Command == 'headers':
            self.HandleBlockHeadersReceived(m.Payload)
        elif m.Command == 'addr':
            self.HandlePeerInfoReceived(m.Payload)
        else:
            self.Log("Command %s not implemented " % m.Command)


    def ProtocolReady(self):
        self.AskForMoreHeaders()
#        self.AskForMoreBlocks()
#        self.RequestPeerInfo()

    def AskForMoreHeaders(self):
        self.Log("asking for more headers...")
        get_headers_message = Message("getheaders", GetBlocksPayload(BC.Default().CurrentHeaderHash()))
        self.SendSerializedMessage(get_headers_message)

    def AskForMoreBlocks(self):
        bcplus_one = BC.Default().CurrentBlockHashPlusOne()

        if bcplus_one is not None and len(self.myblockrequests) < self.leader.BREQMAX:
            self.Log("asking for more blocks ... %s " % (bcplus_one))
            get_blocks_message =  Message("getblocks", GetBlocksPayload(BC.Default().CurrentBlockHashPlusOne()))
            self.SendSerializedMessage(get_blocks_message)

    def RequestPeerInfo(self):
        self.SendSerializedMessage(Message('getaddr'))

    def HandlePeerInfoReceived(self, payload):

        addrs = IOHelper.AsSerializableWithType(payload,'neo.Network.Payloads.AddrPayload.AddrPayload')

        for nawt in addrs.NetworkAddressesWithTime:
            self.leader.RemoteNodePeerReceived(nawt.Address, nawt.Port)


    def SendPeerInfo(self):


        self.Log("SENDING PEER INFO %s " % self)

        peerlist = []
        for peer in self.leader.Peers:
            peerlist.append( peer.GetNetworkAddressWithTime())

        self.Log("Peer list %s " % peerlist)

        addrpayload = AddrPayload(addresses=peerlist)
        message = Message('addr',addrpayload)
#        self.SendSerializedMessage(message)
#       dont send peer info now

    def SendVersion(self):
        m = Message("version", VersionPayload(Settings.NODE_PORT, self.nodeid, Settings.VERSION_NAME))
        self.SendSerializedMessage(m)


    def HandleVersion(self, payload):
        self.Version = IOHelper.AsSerializableWithType(payload, "neo.Network.Payloads.VersionPayload.VersionPayload")
        self.remote_nodeid = self.Version.Nonce
        self.Log("Remote version %s " % vars(self.Version))
        self.SendVersion()

    def HandleGetAddress(self, payload):


        self.Log("888888888888888************************")
        self.Log("888888888888888*****      HANDLETTTTTTTTT GET ADDRESS!!")
        self.Log("888888888888888************************")
        self.Log("Payload: %s %s" % (payload, vars(payload)))

        return

    def HandleAddr(self, payload):
        self.Log("888888888888888************************")
        self.Log("888888888888888*****      GOT ADDRESS!!")
        self.Log("888888888888888************************")
        self.Log("Payload: %s %s" % (payload, vars(payload)))

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
#            self.Log(("HANDLING BLOCK HASH INVVVVVVVVVVVVV!"))
#            if BC.Default().BlockCacheCount() > 6000:
#                self.__log.debug("************************************************")
#                self.__log.debug("BLOCK CACHE COUNT TOO HIGH, PAUSE FOR NOW")
#                self.__log.debug("********************************************")
#
#                reactor.callLater(60.0, self.HandleBlockHashInventory, inventory)
#            else:

            if len(self.myblockrequests) < self.leader.BREQMAX:
#                reactor.callFromThread(self.GenerateBlockHashInventory)
                #self.Log("GENERATED BLOCK HASHES %s " % len(hashes))
                self.HandleBlockHashInventory(inventory)
#            else:
#                self.Log("WONT ASK FOR MORE BLOCKSSSSSS")



    def SendSerializedMessage(self, message):
        ba = Helper.ToArray(message)
        ba2 = binascii.unhexlify(ba)
        self.transport.write(ba2)
        self.bytes_out += len(ba2)
        del ba
        del ba2


    def HandleConsenusInventory(self, inventory):
#        self.Log("handle consensus not implemented")
        pass

    def HandleTransactionInventory(self, inventory):
#        self.Log("handle transaction not implemented")
        pass

#    @profile


    def RequestMissingBlock(self, hash):
        self.Log("On missing block event! %s " % hash)

        message = Message("getdata", InvPayload(InventoryType.Block, [hash]))
        self.SendSerializedMessage(message)

    def HandleBlockHashInventory(self, inventory):

        hashes = []
        index = 0


#        index = self.leader.Peers.index(self)

        hashstart = BC.Default().Height() + 1
        self.Log("will ask for hash start %s " % hashstart)
        while hashstart < BC.Default().HeaderHeight() and len(hashes) < self.leader.BREQPART:
            hash = BC.Default().GetHeaderHash(hashstart)
            if not hash in BC.Default().BlockRequests() and not hash in self.myblockrequests:
                BC.Default().BlockRequests().append(hash)
                self.myblockrequests.append(hash)
                hashes.append(hash)
            hashstart += 1

        if len(hashes) == 0:

            self.Log("ALL BLOCKS COMPLETE.... Wait for more headers")
            self.AskForMoreHeaders()

        else:
            self.Log("requesting %s hashes  " % len(hashes))

            message = Message("getdata", InvPayload(InventoryType.Block, hashes))
#            reactor.callInThread(self.SendSerializedMessage,message)
            self.SendSerializedMessage(message)


    def HandleBlockHeadersReceived(self, inventory):
        inventory = IOHelper.AsSerializableWithType(inventory, 'neo.Network.Payloads.HeadersPayload.HeadersPayload')

        BC.Default().AddHeaders(inventory.Headers)
        del inventory
        if BC.Default().HeaderHeight() < self.Version.StartHeight:
            self.AskForMoreHeaders()

    def HandleBlockReceived(self, inventory):


#        self.Log("ON BLOCK INVENTORY RECEIVED........... %s " % inventory)

        block = IOHelper.AsSerializableWithType(inventory, 'neo.Core.Block.Block')

#        self.Log("ON BLOCK INVENTORY RECEIVED........... %s " % block.Index)

        blockhash =  block.HashToByteString()

        if blockhash in BC.Default().BlockRequests():
            BC.Default().BlockRequests().remove(blockhash)
        if blockhash in self.myblockrequests:
            self.myblockrequests.remove(blockhash)

        self.leader.InventoryReceived(block)

    def HandleBlockReset(self, hash):
        self.myblockrequests = []

    def Log(self, msg):
        self.__log.debug("%s - %s" % (self.endpoint, msg))