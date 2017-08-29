from twisted.internet.protocol import Protocol
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

from .Payloads.GetBlocksPayload import GetBlocksPayload
from .Payloads.InvPayload import InvPayload
from .Payloads.NetworkAddressWithTime import NetworkAddressWithTime
from .Payloads.VersionPayload import VersionPayload
from .InventoryType import InventoryType

import random

from neo import Settings

@logged
class NeoNode(Protocol):

    Version = None

    leader = None

    def __init__(self):

        from neo.Network.NodeLeader import NodeLeader

        self.leader =NodeLeader.Instance()
        self.nodeid = self.leader.NodeId
        self.remote_nodeid = random.randint(1294967200,4294967200)
        self.endpoint = ''
        self.buffer_in = bytearray()
        self.pm = None
        self.reset_counter = False
        self.myblockrequests=set()
        self.bytes_in = 0
        self.bytes_out = 0

        self.host = None
        self.port = None

        self.Log("CREATED NEO NODE!!!!!!!!! %s " % self.remote_nodeid)



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

        self.leader.AddConnectedPeer(self)

        self.Log("Connection from %s" % self.endpoint)


    def connectionLost(self, reason=None):

#        self.buffer_in = None
#        self.pm = None

        reactor.callInThread(self.ReleaseBlockRequests)
        self.leader.RemoveConnectedPeer(self)

#        self.leader = None
        self.Log("%s disconnected %s" % (self.remote_nodeid, reason))


    def ReleaseBlockRequests(self):
        bcr = BC.Default().BlockRequests
        #
        toremove = []
        for req in bcr:
            if req in self.myblockrequests:
                toremove.append(req)
        [bcr.remove(req) for req in toremove]

        self.myblockrequests = set()

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
                #make this threadsafe
#                reactor.callFromThread(self.CheckMessageData)
                self.CheckMessageData()
            except RecursionError:
                self.Log("Recursion error!!!")
                self.Disconnect()

    def CheckMessageData(self):
        if not self.pm: return

        currentlength = len(self.buffer_in)
        messageExpectedLength = 24 + self.pm.Length
#        percentcomplete = int(100 * (currentlength / messageExpectedLength))
#        self.Log("Receiving %s data: %s percent complete" % (self.pm.Command, percentcomplete))

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
            while len(self.buffer_in) > 24 and not self.reset_counter:
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
            self.HandleBlockReceived(m.Payload)
        elif m.Command == 'headers':
            self.HandleBlockHeadersReceived(m.Payload)
        elif m.Command == 'addr':
            self.HandlePeerInfoReceived(m.Payload)
        else:
            self.Log("Command %s not implemented " % m.Command)


    def ProtocolReady(self):
        self.AskForMoreHeaders()
        self.AskForMoreBlocks()
#        self.RequestPeerInfo()

    def AskForMoreHeaders(self):
        self.Log("asking for more headers...")
        get_headers_message = Message("getheaders", GetBlocksPayload(hash_start=[BC.Default().CurrentHeaderHash]))
        self.SendSerializedMessage(get_headers_message)


    def AskForMoreBlocks(self):
        reactor.callInThread(self.DoAskForMoreBlocks)

    def DoAskForMoreBlocks(self):

        hashes = []
        hashstart = BC.Default().Height + 1

        if BC.Default().BlockSearchTries > 400 and len(BC.Default().BlockRequests) > 0:
            self.leader.ResetBlockRequestsAndCache()

        first=None
        while hashstart < BC.Default().HeaderHeight and len(hashes) < self.leader.BREQPART:
            hash = BC.Default().GetHeaderHash(hashstart)
            if hash is not None and not hash in BC.Default().BlockRequests and not hash in self.myblockrequests:
                if not first:
                    first = hashstart
                BC.Default().BlockRequests.add(hash)
                self.myblockrequests.add(hash)
                hashes.append(hash)
            hashstart += 1

        self.Log("asked for more blocks ... %s thru %s stale count %s " % (first,hashstart, BC.Default().BlockSearchTries))


        if len(hashes) > 0:
            message = Message("getdata", InvPayload(InventoryType.Block, hashes))
            self.SendSerializedMessage(message)
        else:
            reactor.callLater(5, self.AskForMoreBlocks)

    def RequestPeerInfo(self):
        self.SendSerializedMessage(Message('getaddr'))

    def HandlePeerInfoReceived(self, payload):

        addrs = IOHelper.AsSerializableWithType(payload,'neo.Network.Payloads.AddrPayload.AddrPayload')

        for nawt in addrs.NetworkAddressesWithTime:
            self.leader.RemoteNodePeerReceived(nawt.Address, nawt.Port)


    def SendPeerInfo(self):


#        self.Log("SENDING PEER INFO %s " % self)

#        peerlist = []
#        for peer in self.leader.Peers:
#            peerlist.append( peer.GetNetworkAddressWithTime())
#        self.Log("Peer list %s " % peerlist)

#        addrpayload = AddrPayload(addresses=peerlist)
#        message = Message('addr',addrpayload)
#        self.SendSerializedMessage(message)
#       dont send peer info now
        pass

    def SendVersion(self):
        m = Message("version", VersionPayload(Settings.NODE_PORT, self.nodeid, Settings.VERSION_NAME))
        self.SendSerializedMessage(m)


    def HandleVersion(self, payload):
        self.Version = IOHelper.AsSerializableWithType(payload, "neo.Network.Payloads.VersionPayload.VersionPayload")
        self.remote_nodeid = self.Version.Nonce
        self.Log("Remote version %s " % vars(self.Version))
        self.SendVersion()

    def HandleVerack(self):
        m = Message('verack')
        self.SendSerializedMessage(m)
        self.ProtocolReady()

    def HandleInvMessage(self, payload):

        inventory = IOHelper.AsSerializableWithType(payload, 'neo.Network.Payloads.InvPayload.InvPayload')

#        print("handle inv %s " % inventory.Type)
#        if inventory.Type == InventoryType.Block:
#            print("handle block ?...")

    def SendSerializedMessage(self, message):
        ba = Helper.ToArray(message)
        ba2 = binascii.unhexlify(ba)
        self.bytes_out += len(ba2)
        self.transport.write(ba2)


    def HandleBlockHeadersReceived(self, inventory):

        self.leader.is_requesting_headers = False
        inventory = IOHelper.AsSerializableWithType(inventory, 'neo.Network.Payloads.HeadersPayload.HeadersPayload')


        BC.Default().AddHeaders(inventory.Headers)
        if BC.Default().HeaderHeight < self.Version.StartHeight:
            self.AskForMoreHeaders()

    def HandleBlockReceived(self, inventory):

        block = IOHelper.AsSerializableWithType(inventory, 'neo.Core.Block.Block')

        blockhash =  block.Hash.ToBytes()

        if blockhash in BC.Default().BlockRequests:
            BC.Default().BlockRequests.remove(blockhash)
        if blockhash in self.myblockrequests:
            self.myblockrequests.remove(blockhash)

        self.leader.InventoryReceived(block)

        if len(self.myblockrequests) < self.leader.NREQMAX:
            self.AskForMoreBlocks()


    def HandleBlockReset(self, hash):
        self.myblockrequests = []

    def Log(self, msg):
        self.__log.debug("%s - %s" % (self.endpoint, msg))