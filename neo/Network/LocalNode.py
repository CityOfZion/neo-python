import socketserver
import threading
import uuid
from neo import Settings
from neo.Network.TCPRemoteNode import TCPListener,TCPRemoteNode
from neo.Network.IPEndpoint import IPEndpoint
from neo.Core.Blockchain import Blockchain
from events import Events
import asyncio

class LocalNode():

    PROTOCOL_VERSION = 0
    CONNECTED_MAX = 10
    UNCONNECTED_MAX = 1000
    MEMORY_POOL_SIZE = 30000


    InventoryReceiving = Events()
    InventoryReceived = Events()

    _mempool = {}           #  contains { uint256, transaction }
    _hash_set = set()       # contains transactions
    _known_hashes = set()   # contains transaction hashes (uint256)

    _cache = None

    _unconnected_peers = set()      #ip enpoints
    _bad_peers = set()              #ip endpoints
    _connected_peers = []           #remote nodes

    _local_addresses = set()        #ip addresses
    _port = Settings.NODE_PORT
    _localhost = '127.0.0.1'

    _nonce = uuid.uuid1()

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
    UserAgent = "NEO Python v0.01"

    def __init__(self):

        print("nonce: %s " % self._nonce)
#        self._make_server()
        self._make_loops()
        #not sure exactly how this works at the moment
        Blockchain.PersistCompleted += self.Blockchain_persistCompleted



    def AcceptPeersAsync(self):

        while self._disposed == 0:

            sock = None

            try:

                socket_future = yield from asyncio.wait_for( self._listener.AcceptPeersAsync())

                socket = socket_future.result()

                print("Socket: %s " % socket)

            except Exception as e:
                print("couldnt get socket %s " % e)
        pass

    def _make_server(self):
        #        self._server = TCPServer((self._localhost, self._port), ThreadedTCPRequestHandler)
        # ip, port = self._server.server_address

        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        #       self._server_thread = threading.Thread(target=self._server.serve_forever, name="LocalNode.TPCServerLoop")
        # Exit the server thread when the main thread terminates
        #       self._server_thread.daemon = True
        #       self._server_thread.start()

        pass

    def _make_loops(self):


        self._connect_thread = threading.Thread(target=self.ConnectToPeersLoop, name='LocalNode.ConnectToPeersLoop')
        self._connect_thread.daemon = True
#        self._connect_thread.start()

        self._pool_thread = threading.Thread(target=self.AddTransactionLoop, name='LocalNode.AddTransactionLoop')
        self._pool_thread.daemon = True
#        self._pool_thread.start()


    def _close(self):
        self._server.shutdown()
        self._server.server_close()

    def LocalAddresses(self):
        return set()

    def ConnectedPeers(self):
        return []

    def RemoteNodeCount(self):
        return len(self._connected_peers)


    def AddTransactionLoop(self):

        pass

    def ConnectToPeersLoop(self):

#        self._server_socket = socket.socket(socket.)
#       while self._disposed == 0:

#            socket = self._so
        pass


    def onPersistCompleted(self, block):
        pass

    def Blockchain_persistCompleted(self, block):

        pass





    async def _startTask(self, future, port, ws_port):

        try:
            ipaddr = self.LocalAddresses()[0]
            ## no UPNP for now

        except Exception as e:
            pass

        self._connect_thread.start()
        self._pool_thread.start()

        if port > 0:
            endpoint = IPEndpoint(IPEndpoint.ANY,port)
            self._listener = TCPRemoteNode(self, endpoint)
            self._listener.daemon_threads = True
            try:
                self._port = port
                self.AcceptPeersAsync()
            except Exception as e:
                print("ecxpetion creating listener: %s " % e)

        if ws_port > 0:
            # create websocket host
            pass



    def Start(self, port=0, ws_port=0):
        if self._started == 0:
            loop = asyncio.get_event_loop()
            future = asyncio.Future()
            asyncio.ensure_future(self._startTask(future, port, ws_port))
            loop.run_until_complete(future)



    def SyncronizeMemoryPool(self):
        #lock connected peers

        for node in self._connected_peers:
            node.RequestMemoryPool()
