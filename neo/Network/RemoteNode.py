# -*- coding:utf-8 -*-


from neo.Network.RPC.RpcClient import RpcClient
from neo.Defaults import TEST_NODE
from datetime import datetime,timedelta
from events import Events
from neo.Core.Blockchain import Blockchain
from .IPEndpoint import IPEndpoint
from .InventoryType import InventoryType
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
from .Message import Message
from neo.Core.TX.MinerTransaction import MinerTransaction
from neo.Core.TX.Transaction import Transaction
from neo.IO.Helper import AsSerializableWithType
import asyncio
from gevent import monkey
import pprint
monkey.patch_all()

class RemoteNode(object):
    """docstring for RemoteNode"""


    Disconnected = Events()
    InventoryReceived = Events()
    PeersReceived = Events()

    HalfMinute = 30
    OneMinute = 60
    HalfHour = 1800


    _message_queue = []
    _missions_global = set() #stores UInt256 hashes
    _missions = set()        #stores UInt256 hashes

    _local_node = None
    _disposed = 0
    _bloom = None


    Version = None           # VersionPayload
    RemoteEndpoint = None           # IPEndpoint
    ListenerEndpoint = None         # IPEndpoint


    def __init__(self, local_node):
        print("creating remote node!")
        self._local_node = local_node


    def Disconnect(self, error):
        if self._disposed == 0:

            self.Disconnected.on_change(self, error)

            #lock missions global
            #lock missions
            self._missions_global.remove(self._missions)
            #end lock missions
            #end lock missions global


    def Dispose(self):
        self.Disconnect(False)


    def EnqueueMessage(self, command, payload=None, is_single=False):

        print("ENQUEUEINGMESSSSSSSAGE:: %s " % command)
        message = Message(command,payload)
        self._message_queue.append(message)
        print("MESSAGE QUEUE LENGTH: %s " % len(self._message_queue))

    def OnAddrMessageReceived(self, payload):
        allpeers = [p.Endpoint for p in payload.AddressList]
        peers = []
        for peer in allpeers:
            if peer.Port != self._local_node.Port and not peer.address in self._local_node.LocalAddresses:
                peers.append(peer)
        if len(peers):
            self.PeersReceived.on_change(self, peers)


    def OnFilterAddMessageReceived(self, payload):
        if self._bloom is not None:
            self._bloom.Add(payload.Data)


    def OnFilterClearMessageReceived(self):
        self._bloom = None

    def onFilterLoadMessageReceived(self, payload):
#        bloom_filter = BloomFilter(payload.Filter.Length * 8, payload.K, payload.Tweak, payload.Filter);
        pass

    def OnGetAddrMessageReceived(self):
        if not self._local_node.ServiceEnabled: return

        payload = None

        #lock self._localnode.ConnectedPeers

        plist = [peer for peer in self._local_node.ConnectedPeers() if peer.ListenerEndpoint is not None and peer.Version is not None][:100]

        naddrlist = [ NetworkAddressWithTime(peer.ListenerEndpoint, peer.Version.Services, peer.Version.Timestamp) for peer in plist]

        payload = AddrPayload(naddrlist)

        #endlock

        self.EnqueueMessage("addr",payload)

    def OnGetBlocksMessageReceived(self, payload):

        if not self._local_node.ServiceEnabled or Blockchain.Default() is None: return

        phashes = [Blockchain.Default().GetHeader(p) for p in payload.HashStart if Blockchain.Default().GetHeader(p) is not None]
        sorted(phashes, key=lambda p: p.Index)

        if len(phashes) < 1: return

        hash = phashes[0]

        if hash == payload.HashStop: return

        hashes = []

        while hash != payload.HashStop and len(hashes) < 500:

            hash = Blockchain.Default().GetNextBlockHash(hash)

            if hash is None: break

            hashes.append(hash)


        self.EnqueueMessage('inv', InvPayload(InventoryType.Block, hashes))


    def OnGetDataMessageReceived(self, payload):

        print("ON GETTTTTT DAAT MESSSAGE RCEEEEEEEVVEED")
        for hash in payload.DistinctHashes():


            inventory = None
            #no caching for now
            #if (!localNode.RelayCache.TryGet(hash, out inventory) & & !localNode.ServiceEnabled)
            #continue;

            if payload.Type == InventoryType.TX:


                inventory = self._local_node.GetTransaction(hash)
                if inventory is None and Blockchain.Default() is not None:
                    inventory = Blockchain.Default().GetTransanction(hash)
                if inventory is not None:
                    self.EnqueueMessage('tx',inventory)

            elif payload.Type == InventoryType.Block:

                if Blockchain.Default() is not None:
                    inventory = Blockchain.Default().GetBlock(hash)

                if inventory is not None:
                    self.EnqueueMessage('block',inventory)

                #ignore bloom filter for now


            elif payload.Type == InventoryType.Consensus:

                if inventory is not None:
                    self.EnqueueMessage('consensus', inventory)



    def OnGetHeadersMessageReceived(self, payload):
        if not self._local_node.ServiceEnabled or Blockchain.Default() is None: return

        phashes = [Blockchain.Default().GetHeader(p) for p in payload.HashStart if
                   Blockchain.Default().GetHeader(p) is not None]
        sorted(phashes, key=lambda p: p.Index)

        if len(phashes) < 1: return

        hash = phashes[0]

        if hash == payload.HashStop: return

        headers = []

        while hash != payload.HashStop and len(headers) < 2000:

            hash = Blockchain.Default().GetNextBlockHash(hash)

            if hash is None: break

            headers.append(hash)

        self.EnqueueMessage('headers', InvPayload(InventoryType.Block, headers))


    def OnHeadersMessageReceived(self, payload):
        if Blockchain.Default() is None: return

        Blockchain.Default().AddHeaders(payload.Headers)

        if Blockchain.Default().HeaderHeight() < self.Version.StartHeight:
            self.EnqueueMessage("getheaders", GetBlocksPayload(Blockchain.Default().CurrentHeaderHash()))


    def OnInventoryReceived(self, inventory):

        print("ON INVENTORY RECEIVED!!!!")
        #lock missions global
        self._missions_global.remove( inventory.Hash)
        #endlock

        #lock missions
        self._missions.remove( inventory.Hash )
        #endlock

        if inventory is MinerTransaction: return

        self.InventoryReceived.on_change(self, inventory)


    def OnInvMessageReceived(self, payload):

        print("ON INV MESSAGE RECEIVED: %s  %s" % (payload.Type, type(InventoryType.Block)))

        if not payload.Type in InventoryType.AllInventoriesInt():
            return

        print("on inv received!")
        hashes = payload.DistinctHashes()
        print("payload hashes: %s " % hashes)
        #lock localnode.knownhashes

        hashes = [h for h in hashes if not h in self._local_node.KnownHashes()]
        #endlock

        if len(hashes) < 1:
            print("hash len is zero, nothing to do")
            return

        #lock missions global
        if self._local_node.GlobalMissionsEnabled:
            print("getting hashes from missions global")
            hashes = [h for h in hashes if not h in self._missions_global]
        print("adding hashes to missions global")
        [self._missions_global.add(h) for h in hashes]
        #endlock

        #lock missions
        print("adding hashes to missions")
        [self._missions.add(h) for h in hashes]
        #endlock
        print("added hashes to missions")
        if len(hashes) < 1: return
        print("hashes: %s " % hashes)
        self.EnqueueMessage("getdata", InvPayload(payload.Type, hashes))


    def OnMemPoolMessageReceived(self):
        self.EnqueueMessage("inv", InvPayload(InventoryType.TX, [hash for hash in self._local_node.GetMemoryPool()]))



    def OnMessageReceived(self, message):

        print("ON MESSAGE RECEIVED:::::::::: %s " % message.Command)
        if message.Command == "addr":
            self.OnAddrMessageReceived( AsSerializableWithType(message.Payload, 'neo.Network.Payloads.AddrPayload.AddrPayload') )

        elif message.Command == "block":
            self.OnInventoryReceived( AsSerializableWithType(message.Payload, 'neo.Core.Block.Block'))

        elif message.Command == 'consensus':
            self.OnInventoryReceived(AsSerializableWithType(message.Payload, 'neo.Network.Payloads.ConsensusPayload.ConsensusPayload'))

        elif message.Command == 'filteradd':
            pass

        elif message.Command == 'filterclear':
            pass

        elif message.Command == 'filterload':
            pass

        elif message.Command == 'getaddr':
            self.OnGetAddrMessageReceived()

        elif message.Command == 'getblocks':
            self.OnGetBlocksMessageReceived(AsSerializableWithType(message.Payload, 'neo.Network.Payloads.GetBlocksPayload.GetBlocksPayload'))

        elif message.Command == 'getdata':
            self.OnGetDataMessageReceived(AsSerializableWithType( message.Payload, 'neo.Network.Payloads.InvPayload.InvPayload'))

        elif message.Command == 'getheaders':
            self.OnGetHeadersMessageReceived(AsSerializableWithType(message.Payload, 'neo.Network.Payloads.GetBlocksPayload.GetBlocksPayload'))

        elif message.Command == 'headers':
            self.OnHeadersMessageReceived(AsSerializableWithType(message.Payload, 'neo.Network.Payloads.HeadersPayload.HeadersPayload'))

        elif message.Command == 'inv':
            self.OnInvMessageReceived( AsSerializableWithType(message.Payload, 'neo.Network.Payloads.InvPayload.InvPayload'))

        elif message.Command == 'mempool':
            self.OnMemPoolMessageReceived()

        elif message.Command == 'tx':
            if len(message.Payload) < 1024 * 1024:
                self.OnInventoryReceived(Transaction.DeserializeFrom(message.Payload))


        elif message.Command in ['verack','version',]:
            self.Disconnect(True)


        elif message.Command in ["alert","merkleblock","notfound","ping","pong","reject",]:
            pass



    def ReceiveMessageAsync(self, timeout):
        #abstract

        pass

    def SendMessageAsync(self, message):
        #abstract
        pass



    def RequestMemoryPool(self):
        self.EnqueueMessage("mempool", None, True)

    def RequestPeers(self):
        self.EnqueueMessage("getaddr",None,True)



    def Relay(self, data):

        if not self.Version.Relay: return False

        #check if data is IInventory
        if getattr(data, 'InventoryType'):
            #bloom filter stuff... ignore for now

            self.EnqueueMessage("inv", InvPayload(data.InventoryType, data.Hash))
            return True

        #or list of TX
        else:

            try:
                if data[0] is Transaction:

                    hashes = [tx.Hash() for tx in data]

                    if len(hashes):

                        self.EnqueueMessage("inv", InvPayload(InventoryType.TX, hashes))
                        return True
            except Exception as e:
                print("couldn't get transactions from data list :%s " % e)

        return False


    async def StartProcol(self):
        print("starting protocol!!!!: %s" % self.ListenerEndpoint.ToAddress())

        message = Message("version", VersionPayload(self._local_node._port, self._local_node._nonce, self._local_node.UserAgent))
        result_future = await asyncio.wait_for(self.SendMessageAsync(message), 60.0)
        print("result::: %s " % result_future)
        if not result_future: return

        message_rec = await asyncio.wait_for(self.ReceiveMessageAsync(self.HalfMinute), 60.0)
        print("message: :%s" % message_rec)

        if message_rec is None: return

        print("message recieved: %s " % message_rec.Command)
        if message_rec.Command != 'version':
            print("command is not version...., disconnecting")
            self.Disconnect(True)
            return


        try:
            self.Version = AsSerializableWithType(message.Payload, "neo.Network.Payloads.VersionPayload.VersionPayload")

        except Exception as e:
            print("exception getting version: %s " % e)
            self.Disconnect(e)
            return

        if self.Version.Nonce != self._local_node._nonce:
            print("unequal nonces: %s %s " % (self.Version.Nonce, self._local_node._nonce))
            self.Disconnect(True)
            return

        #lock localnode connected peers
#        if (localNode.connectedPeers.Where(p= > p != this).Any(p= > p.RemoteEndpoint.Address.Equals(
#                RemoteEndpoint.Address) & & p.Version?.Nonce == Version.Nonce))
#        {
#            Disconnect(false);
#        return;
#        }

        #endlock

        print("continuing... listener endpoint, port: %s %s " % (self.ListenerEndpoint.Port, self.Version.Port))

        if self.ListenerEndpoint is not None:
            if self.ListenerEndpoint.Port != self.Version.Port:
                print("unequal ports....")
                self.Disconnect(True)
                return
        elif self.Version.Port > 0:
            self.ListenerEndpoint = IPEndpoint(self.RemoteEndpoint.Address, self.Version.Port)

        print("will wait to send verack message")

        verack= await asyncio.wait_for( self.SendMessageAsync(Message("verack")), 60.0)

        if verack is None or verack is False:
            print("verack is none...")
            return
        else:
            print("VERACK: %s " % verack)

        vmessage = await asyncio.wait_for( self.ReceiveMessageAsync(self.HalfMinute), 60.0)

        print("vmessage future command: %s" % (vmessage) )
        if vmessage is None or vmessage.Command != "verack":
            print("verack command failed .... disconnet" )
            self.Disconnect(True)
            return

        if Blockchain.Default().HeaderHeight() < self.Version.StartHeight:

            self.EnqueueMessage("getheaders", GetBlocksPayload(Blockchain.Default().CurrentHeaderHash()),True)

        sendloop = asyncio.run_coroutine_threadsafe(self.StartSendLoop(), asyncio.get_event_loop())

        print("AFTER SENDLOOPPP")

        while self._disposed == 0:

            if Blockchain.Default() is not None:

                if len(self._missions)  == 0 and Blockchain.Default().Height() < self.Version.StartHeight:
                    self.EnqueueMessage("getblocks", GetBlocksPayload(Blockchain.Default().CurrentBlockHash()), True)

            timeout = self.HalfHour if len(self._missions) == 0 else self.OneMinute

            receive_message_future = await asyncio.wait_for( self.ReceiveMessageAsync(timeout), 10)

            if not receive_message_future:
                print("no message future!: ")
                break

            try:
                self.OnMessageReceived(receive_message_future)
            except Exception as e:
                print("could not receive message: %s " % e)
                self.Disconnect(True)
                break


    @asyncio.coroutine
    def StartSendLoop(self):
        print("STARTING SEND LOOP")
        while self._disposed == 0:

            message = None

            #lock message queue
            print("MESSAGE QUEUE %s " % len(self._message_queue))
            print("Commands: %s " % [m.Command for m in self._message_queue])
            if len(self._message_queue) > 0:

                message = self._message_queue[0]
                self._message_queue.remove(message)
                print("WILL SEND MESSAGE:::: %s " % message.Command)

            if message is None:
#                i = 0
#                while i < 10 and self._disposed == 0:
#                    i = i +1
                print("Send loop sleep!")
                yield from asyncio.sleep(1)

            else:
                print("STARTSENDLOOPMESSAGE NOT NONE, SENDIT: ... %s " % message.Command)
                msend = yield from asyncio.wait_for( self.SendMessageAsync(message), 10)

