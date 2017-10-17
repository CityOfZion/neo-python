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

        self.ReleaseBlockRequests()
        self.leader.RemoveConnectedPeer(self)
        self.Log("%s disconnected %s" % (self.remote_nodeid, reason))


    def ReleaseBlockRequests(self):
        bcr = BC.Default().BlockRequests
        requests = self.myblockrequests
        self.Log("Release block requests before %s " % len(bcr))
        #
        for req in requests:
            try:
                bcr.remove(req)
            except Exception as e:
                self.Log("Couldnt remove request %s " % e)
        self.Log("Release block requests after %s " % len(bcr))

        self.myblockrequests = set()


    def dataReceived(self, data):

        self.bytes_in += (len(data))

        self.buffer_in = self.buffer_in + data

        self.CheckDataReceived()

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
            except Exception as e:
                print("Could not check message data %s " % e)

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
            if len(self.buffer_in) > 24 and not self.reset_counter:
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
        elif m.Command == 'getdata':
            self.HandleGetDataMessageReceived(m.Payload)
        elif m.Command == 'inv':
            self.HandleInvMessage(m.Payload)
        elif m.Command == 'block':
            self.HandleBlockReceived(m.Payload)
        elif m.Command == 'headers':
            reactor.callFromThread(self.HandleBlockHeadersReceived, m.Payload)
#            self.HandleBlockHeadersReceived(m.Payload)
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
        current_header_height = BC.Default().HeaderHeight

        do_go_ahead = False
        if BC.Default().BlockSearchTries > 400 and len(BC.Default().BlockRequests) > 0:
            do_go_ahead = True

        first=None
        while hashstart < current_header_height and len(hashes) < self.leader.BREQPART:
            hash = BC.Default().GetHeaderHash(hashstart)
            if not do_go_ahead:
                if hash is not None and not hash in BC.Default().BlockRequests and not hash in self.myblockrequests:
                    if not first:
                        first = hashstart
                    BC.Default().BlockRequests.add(hash)
                    self.myblockrequests.add(hash)
                    hashes.append(hash)
            else:
                if not first:
                    first = hashstart
                BC.Default().BlockRequests.add(hash)
                self.myblockrequests.add(hash)
                hashes.append(hash)

            hashstart += 1

        self.Log("asked for more blocks ... %s thru %s (%s blocks) stale count %s BCRLen: %s " % (first,hashstart, len(hashes), BC.Default().BlockSearchTries, len(BC.Default().BlockRequests)))


        if len(hashes) > 0:
            message = Message("getdata", InvPayload(InventoryType.Block, hashes))
            self.SendSerializedMessage(message)
        else:
            self.Log("all caught up!!!!!! hashes is zero")
            self.AskForMoreHeaders()
            reactor.callLater(20, self.DoAskForMoreBlocks)

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

    def RequestVersion(self):
        m = Message("getversion")
        self.SendSerializedMessage(m)

    def SendVersion(self):
        m = Message("version", VersionPayload(Settings.NODE_PORT, self.remote_nodeid, Settings.VERSION_NAME))
        self.SendSerializedMessage(m)


    def HandleVersion(self, payload):
        self.Version = IOHelper.AsSerializableWithType(payload, "neo.Network.Payloads.VersionPayload.VersionPayload")
        self.nodeid = self.Version.Nonce
        self.Log("Remote version %s " % vars(self.Version))
        self.SendVersion()

    def HandleVerack(self):
        m = Message('verack')
        self.SendSerializedMessage(m)
        self.ProtocolReady()

    def HandleInvMessage(self, payload):
        pass


    def SendSerializedMessage(self, message):
        ba = Helper.ToArray(message)
        ba2 = binascii.unhexlify(ba)
        self.bytes_out += len(ba2)
        self.transport.write(ba2)


    def HandleBlockHeadersReceived(self, inventory):

        inventory = IOHelper.AsSerializableWithType(inventory, 'neo.Network.Payloads.HeadersPayload.HeadersPayload')

        if inventory is not None:
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
            self.DoAskForMoreBlocks()


    def HandleBlockReset(self, hash):
        self.myblockrequests = []


    def HandleGetDataMessageReceived(self, payload):

        inventory = IOHelper.AsSerializableWithType(payload, 'neo.Network.Payloads.InvPayload.InvPayload')


        for hash in inventory.Hashes:
            hash = hash.encode('utf-8')

            item = None
            #try to get the inventory to send from relay cache

            if hash in self.leader.RelayCache.keys():
                item = self.leader.RelayCache[hash]

            if item:
                if inventory.Type == int.from_bytes( InventoryType.TX,'little'):

                    message = Message(command='tx',payload=item, print_payload=True)
                    self.SendSerializedMessage(message)

                elif inventory.Type == int.from_bytes( InventoryType.Block, 'little'):
                    print("handle block!")

                elif inventory.Type == int.from_bytes( InventoryType.Consensus, 'little'):
                    print("handle consensus")


    def Relay(self, inventory):

        inventory = InvPayload(type=inventory.InventoryType, hashes=[inventory.Hash.ToBytes()])
        m = Message("inv", inventory)
        self.SendSerializedMessage(m)

        return True

    def Log(self, msg):
        self.__log.debug("%s - %s" % (self.endpoint, msg))