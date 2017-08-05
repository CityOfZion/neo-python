from neo import Settings
from neo.Network.TCPRemoteNode import TCPRemoteNode
from neo.Network.IPEndpoint import IPEndpoint
from neo.Core.Blockchain import Blockchain
from neo.Core.Block import Block
from neo.Core.TX.MinerTransaction import MinerTransaction
from neo.Core.TX.Transaction import Transaction,TransactionType
from events import Events
import asyncio
from gevent import monkey
from concurrent.futures import ThreadPoolExecutor
monkey.patch_all()
import random
import threading
from autologging import logged

#outside class def so it can be static
_mempool = {}  # contains { uint256, transaction }

@logged
class LocalNode():

    PROTOCOL_VERSION = 0
    CONNECTED_MAX = 10
    UNCONNECTED_MAX = 1000
    MEMORY_POOL_SIZE = 30000



    __LOOP = None

    InventoryReceiving = Events()
    InventoryReceived = Events()

#    new_tx_event = threading.Event()

    _temppool = set()       # contains transactions
    _hash_set = set()       # contains transactions
    _known_hashes = []   # contains transaction hashes (uint256)

    _cache = None

    _unconnected_peers = set()      #ip enpoints
    _bad_peers = set()              #ip endpoints
    _connected_peers = []           #remote nodes

    _local_addresses = set()        #ip addresses
    _port = 0
    _localhost = '127.0.0.1'

    _nonce = random.randint(1294967200,4294967200)

    _listener = None

    _server_thread = None
    _connect_thread = None
    _pool_thread = None

    _server_socket = None
    _server = None

    _started = 0
    _disposed = 0

    GlobalMissionsEnabled = True
    ServiceEnabled = True
    UnPnpEnabled = False
    UserAgent = "/NEO:2.0.1/"

    def __init__(self):

#        self._make_server()

        self._port = Settings.NODE_PORT
        self._make_loops()
        #not sure exactly how this works at the moment
        Blockchain.PersistCompleted.on_change += self.Blockchain_persistCompleted



    def AcceptPeersAsync(self):

        while self._disposed == 0:

            sock = None

            try:

                sock, addr = self._listener.AcceptSocketAsync()

                remoteNode = TCPRemoteNode(self, addr)

            except Exception as e:
                print("couldnt get socket %s " % e)
        pass

    def AddTransaction(self, tx):
        if Blockchain.Default() is None: return False

        #lock mempool

        if tx.Hash() in _mempool:
            return False
        elif Blockchain.Default().ContainsTransaction(tx.Hash()):
            return False
        elif not tx.Verify([v for k,v in _mempool]): return False

        _mempool[tx.Hash()] = tx
        # endlock

        self.CheckMemPool()

        return True


    def _make_loops(self):


        self.__LOOP = asyncio.new_event_loop()
        asyncio.set_event_loop(self.__LOOP)
        asyncio.run_coroutine_threadsafe(self.ConnectToPeersLoop(), self.__LOOP)

        asyncio.run_coroutine_threadsafe(self.AddTransactionLoop(), self.__LOOP)
        self.__LOOP.run_forever()



    def _close(self):
        self._server.shutdown()
        self._server.server_close()

    def LocalAddresses(self):
        return set()

    def ConnectedPeers(self):
        return []

    def RemoteNodeCount(self):
        return len(self._connected_peers)


    async def AddTransactionLoop(self):
#        self.new_tx_event.wait()

        self.__log.debug("Running add transaction loop")
        while self._disposed == 0:
            transactions = []

            #lock temppool
            #if len(self._temppool == 0): continue
            transactions = list(self._temppool)
            self._temppool = []
            #endlock

            verified = set()
            #lock mempool

            transactions = [tx for tx in transactions if not tx.Hash() in _mempool and not Blockchain.Default().ContainsTransaction(tx.Hash())]

            if len(transactions):
                mempool_current = [v for k,v in _mempool]
                for tx in transactions:
                    if tx.Verify( mempool_current + transactions):
                        verified.add(tx)
                for tx in verified:
                    _mempool[tx.Hash()] = tx

                self.CheckMemPool()
            #endlock

            await self.RelayDirectly(verified)

            if self.InventoryReceived is not None:
                [self.InventoryReceived.on_change(tx) for tx in verified]


    @staticmethod
    def AllowHashes(hashes):
        #lock known hashes
            LocalNode._known_hashes = LocalNode._known_hashes - hashes
        #endlock


    def KnownHashes(self):
        return self._known_hashes

    def Blockchain_persistCompleted(self, block):
        #lock mempool
        for tx in block.Transactions:
            del _mempool[tx.Hash()]

        if len(_mempool) == 0: return

        remaining = [v for k,v in _mempool]
        _mempool = {}

        #lock temp ppol
        self._temppool = self._temppool + remaining
        #end lock temppool

#        self.new_tx_event.set()
        #endlock mempool


    def CheckMemPool(self):

        if len(_mempool) <= self.MEMORY_POOL_SIZE: return
        num_to_delete = len(_mempool) - self.MEMORY_POOL_SIZE
        hashes_to_delete = [k for k,v in _mempool][:-num_to_delete]
        for hash in hashes_to_delete:
            del _mempool[hash]



#    async def ConnectToPeersAsync(self, address, port):


    async def ConnectToPeersAsync(self, remoteEndpoint):

        if remoteEndpoint.Port == self._port and remoteEndpoint.Address in self.LocalAddresses():
            return

        #lock unconnected peers
        try:
            self._unconnected_peers.remove(remoteEndpoint)
        except Exception as e:
            print("Could not remove endpoint from unconnected peers")
        #endlock

        #lock connected peers
        for cp in self._connected_peers:
            if cp.ListenerEndpoint.Address == remoteEndpoint.Address and cp.ListenerEndpoint.Port == remoteEndpoint.ListenerEndpoint.Port:
                return
        #endlock

        remote_node = TCPRemoteNode(self, remoteEndpoint)

        result = remote_node.ConnectAsync()
        if result:
            await self.OnConnected(remote_node)


    @asyncio.coroutine
    def ConnectToPeersLoop(self):

        while self._disposed == 0:

            connectedCount = len(self._connected_peers)
            unconnectedCount = len(self._unconnected_peers)
            self.__log.debug("connect loop: unconnected, connected %s %s " % (connectedCount, unconnectedCount))
            if connectedCount < self.CONNECTED_MAX:

                taskloop = asyncio.get_event_loop()
                tasks = []

                if unconnectedCount > 0:
                    endpoints = []

                    #lock unconnected peers
                    num_to_take = self.CONNECTED_MAX - connectedCount
                    endpoints = list(self._unconnected_peers)[:num_to_take]
                    #endlock

                    for ep in endpoints:
                        tasks.append( taskloop.create_task( self.ConnectToPeersAsync(ep)))

                elif connectedCount > 0:

                    #lock connected peers
                    [node.RequestPeers() for node in self._connected_peers]
                    #endlock

                else:
                    seeds = [IPEndpoint(str.split(':')[0], int(str.split(':')[1])) for str in Settings.SEED_LIST]
#                    seeds = [IPEndpoint('seed1.neo.org',20333),]

                    for ep in seeds:
                        tasks.append(taskloop.create_task(self.ConnectToPeersAsync(ep)))

                wait_tasks = asyncio.wait(tasks)
                taskloop.run_until_complete(wait_tasks)
                taskloop.close()

            i = 0

            while i < 50 and self._disposed == 0:
                i = i+1
                asyncio.sleep(1)


    @staticmethod
    def ContainsTransaction(self):
        #lock mempool
        return hash in _mempool
        #endlock


    def Dispose(self):
        if self._disposed == 0:

            if self._started  > 0:

                Blockchain.PersistCompleted -= self.Blockchain_persistCompleted

                if self._listener is not None: self._listener.Dispose()

                if self._connect_thread.is_alive(): self._connect_thread.join()

                #lock unconnected peers

                if self._unconnected_peers < self.UNCONNECTED_MAX:
                    #lock connected peers
                    self._unconnected_peers = self._unconnected_peers + [peer for peer in self._connected_peers if peer.ListenerEnpoint is not None][:self.UNCONNECTED_MAX - len(self._unconnected_peers)]
                    #endlock

                nodes = []

                #lock connected peers
                nodes = list(self._connected_peers)
                #endlock

                #this shouldbe done async, i guess
                [node.Disconnect(False) for node in nodes]

                #self.new_tx_event.set()

                if self._pool_thread.is_alive(): self._pool_thread.join()

                #self.new_tx_event.clear()


    @staticmethod
    def GetMemoryPool():
        #lock mempool
        return [v for k,v in _mempool]
        #endlock

    def GetRemoteNodes(self):
        #lock connected peers
        return list(self._connected_peers)
        #endlock

    @staticmethod
    def GetTransaction(hash):

        #lock mempool
        if _mempool[hash] is not None:
            return _mempool[hash]
        #endlock
        return None

    @staticmethod
    def IsIntranetAddress( address ):
        raise NotImplementedError()

    @staticmethod
    def LoadState(stream):
        raise NotImplementedError()

    async def OnConnected(self, remoteNode):

        #lock connected peres
        self._connected_peers.append(remoteNode)
        #endlock
#        self.__log.debug("connected peers: %s " % [p.ToString() for p in self._connected_peers])
        remoteNode.Disconnected.on_change += self.RemoteNode_Disconnected
        remoteNode.InventoryReceived.on_change += self.RemoteNode_InventoryReceived
        remoteNode.PeersReceived.on_change += self.RemoteNode_PeersReceived
        node_name = 'RemoteNode-%s-thread ' % remoteNode.RemoteEndpoint.Address
        loop = asyncio.get_event_loop()
        await loop.create_task(remoteNode.StartProcol())
#        thread = threading.Thread(target=remoteNode.StartProcol,name=node_name, daemon=True)
#        thread.start()
#        await remoteNode.StartProcol()


    async def ProcessWebsocketAsync(self, context):
        raise NotImplementedError()

    def Relay(self, inventory):


        if inventory is MinerTransaction: return False

        #lock known hashes
        if inventory.Hash() in self._known_hashes: return False
        #endlock

        self.InventoryReceiving.on_change(self, inventory)

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


        relayed = self.RelayDirectly(inventory)

        self.InventoryReceived.on_change(inventory)

        return relayed

    def RelayDirectly(self, inventory):

        relayed = False
        #lock connected peers

        #RelayCache.add(inventory)

#        for node in self._connected_peers:
#            self.__log.debug("Relaying to remote node %s " % node)
#            relayed |= node.Relay(inventory)

        #end lock
        return relayed

    def RemoteNode_Disconnected(self, sender, error):
        remoteNode = sender
        remoteNode.Disconnected.on_change -= self.RemoteNode_Disconnected
        remoteNode.InventoryReceived.on_change -= self.RemoteNode_InventoryReceived
        remoteNode.PeersReceived.on_change -= self.RemoteNode_PeersReceived

        if error and remoteNode.ListenerEndpoint is not None:
            #lock bad peers
            self._bad_peers.add(remoteNode.ListenerEndpoint)
            #endlock

            #lock unconnected peers
            #lock connected peers
            if remoteNode.ListenerEndpoint is not None:
                self._unconnected_peers.remove(remoteNode.ListenerEndpoint)

            self._connected_peers.remove(remoteNode)
            #endlock
            #endlock

    def RemoteNode_InventoryReceived(self, sender, inventory):

        self.__log.debug("Remote Node inventory received %s " % inventory)

        if inventory is Transaction and inventory.Type is not TransactionType.ClaimTransaction and inventory.Type is not TransactionType.IssueTransaction:

            if Blockchain.Default() is None: return

            #lock known hashes
            if inventory.Hash in self._known_hashes: return
            self._known_hashes.append(inventory.Hash)
            # endlock

            self.InventoryReceiving.on_change(self, inventory)

            #lock temppool
            self._temppool.add(inventory)
            #endlock
            #self.new_tx_event.set()

        else:
            self.Relay(inventory)

    def RemoteNode_PeersReceived(self, sender, peers):

        #lock unconnected peers


        if len(self._unconnected_peers) < self.UNCONNECTED_MAX:

            #lock bad peers
            #lock connected peers

            self._unconnected_peers = self._unconnected_peers + peers
            self._unconnected_peers -= self._bad_peers
            self._unconnected_peers -= set([p.ListenerEndpoint for p in self._connected_peers])
            #endlock connected peers
            #endlock bad peers


        #endlock unconnected peers


    @staticmethod
    def SaveState( stream ):
        raise NotImplementedError()

    async def _startTask(self, port, ws_port):

        self.__log.debug("__start_task")

        if port > 0:
            endpoint = IPEndpoint(IPEndpoint.ANY,port)
            try:
                self._listener = TCPRemoteNode(self, endpoint)
                self._listener.daemon_threads = True
            except Exception as e:
                print("coludnt start remote node: %s " % e)

            try:
                self._port = port

                executor = ThreadPoolExecutor()
                await self.__LOOP.run_in_executor(executor, self.AcceptPeersAsync())
            except Exception as e:
                print("ecxpetion creating listener: %s " % e)

        if ws_port > 0:
            # create websocket host
            pass



    def Start(self, port=0, ws_port=0):
        if self._started == 0:


            asyncio.run_coroutine_threadsafe(self._startTask(port, ws_port), self.__LOOP)
#            asyncio.ensure_future(self._startTask(port, ws_port))
#            self.__LOOP.run_until_complete(future)
            yield self.__LOOP.run_forever()


    def SyncronizeMemoryPool(self):
        #lock connected peers

        for node in self._connected_peers:
            node.RequestMemoryPool()
