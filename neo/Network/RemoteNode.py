# -*- coding:utf-8 -*-
"""
Description:
    Remote Node, use to broadcast tx
Usage:
    from neo.Network.RemoteNode import RemoteNode
"""


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
from neo.Core.TX.MinerTransaction import MinerTransaction
from neo.Core.TX.Transaction import Transaction
from neo.IO.Helper import AsSerializableWithType



class RemoteNode(object):
    """docstring for RemoteNode"""


    Disconnected = Events()
    InventoryReceived = Events()
    PeersReceived = Events()

    HalfMinute = timedelta(seconds=30)
    OneMinute = timedelta(minutes=1)
    HalfHour = timedelta(minutes=30)


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
        super(RemoteNode, self).__init__()
        self._local_node = local_node



    def Disconnect(self, error):
        if self._disposed == 0:

        self.Disconnected.on_change(error)

        #lock missions global
        #lock missions
        self._missions_global.remove(self._missions)
        #end lock missions
        #end lock missions global


    def Dispose(self):
        self.Disconnect(False)


    def EnqueueMessage(self, command, payload=None, is_single=False):

        self._message_queue.append({'command':command, 'payload':payload})


    def OnAddrMessageReceived(self, payload):
        allpeers = [p.Endpoint for p in payload.AddressList]
        peers = []
        for peer in allpeers:
            if peer.Port != self._local_node.Port and not peer.address in self._local_node.LocalAddresses:
                peers.append(peer)
        if len(peers):
            self.PeersReceived.on_change(peers)


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

        #lock missions global
        self._missions_global.remove( inventory.Hash)
        #endlock

        #lock missions
        self._missions.remove( inventory.Hash )
        #endlock

        if inventory is MinerTransaction: return

        self.InventoryReceived.on_change(inventory)


    def OnInvMessageReceived(self, payload):

        if payload.Type != InventoryType.Block or payload.Type != InventoryType.Consensus or payload.Type != InventoryType.TX:
            return

        hashes = payload.DistinctHashes()

        #lock localnode.knownhashes

        hashes = [h for h in hashes if not h in self._local_node.KnownHashes() ]
        #endlock

        if len(hashes) < 1: return

        #lock missions global
        if self._local_node.GlobalMissionsEnabled:
            hashes = [h for h in hashes if not h in self._missions_global]
        self._missions_global.add(hashes)
        #endlock

        #lock missions
        self._missions.add(hashes)
        #endlock

        if len(hashes) < 1: return

        self.EnqueueMessage("getdata", InvPayload(payload.Type, hashes))


    def OnMemPoolMessageReceived(self):
        self.EnqueueMessage("inv", InvPayload(InventoryType.TX, [hash for hash in self._local_node.GetMemoryPool()]))



    def OnMessageReceived(self, message):

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


    def sendRawTransaction(self, tx):
        """
        Send Transaction
        """
        return self.rpc.call(method="sendrawtransaction",
                             params=[tx])

    def getBestBlockhash(self):
        """
        Get Best BlockHash from chain
        """
        return self.rpc.call(method="getbestblockhash",
                             params=[]).get("result", "")

    def getBlock(self, hint, verbose=1):
        """
        Get Block from chain with hash or index
        hint : blockhash or index
        Verbose: 0-Simple, 1-Verbose
        """
        if verbose not in (0, 1):
            raise ValueError('verbose, should be 0 or 1.')
        return self.rpc.call(method="getblock",params=[hint, verbose])

    def getBlockCount(self):
        """
        Get Block Count from chain
        """
        return self.rpc.call(method="getblockcount",
                             params=[]).get('result', 0)

    def getBlockHash(self, index):
        """
        Get BlockHash from chain by index
        """
        return self.rpc.call(method="getblockhash",
                             params=[index]).get('result', '')

    def getConnectionCount(self):
        """
        Get Connection Count from chain
        """
        return self.rpc.call(method="getconnectioncount",
                             params=[]).get('result', 0)

    def getRawMemPool(self):
        """
        Get Uncomfirmed tx in Memory Pool
        """
        return self.rpc.call(method="getrawmempool",
                             params=[])

    def getRawTransaction(self, txid, verbose=0):
        """
        Get comfirmed tx from chain
        Verbose: 0-Simple, 1-Verbose
        """
        if verbose not in (0, 1):
            raise ValueError('verbose, should be 0 or 1.')

        return self.rpc.call(method="getrawtransaction",
                             params=[txid, verbose])

    def getTxOut(self, txid, n=0):
        """
        Get Tx Output from chain
        """
        return self.rpc.call(method="gettxout",
                             params=[txid, n])
