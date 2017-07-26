import socketserver
import threading
import uuid
from neo import Settings
from neo.Network.TCPListener import TCPServer,ThreadedTCPRequestHandler
from neo.Core.Blockchain import Blockchain
from events import Events

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
        self._start_server()
        self._start_loops()
        #not sure exactly how this works at the moment
        Blockchain.OnPersistCompleted()

    def _start_server(self):


        self._server = TCPServer((self._localhost, self._port), ThreadedTCPRequestHandler)
        #ip, port = self._server.server_address

        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        self._server_thread = threading.Thread(target=self._server.serve_forever, name="LocalNode.TPCServerLoop")
        # Exit the server thread when the main thread terminates
        self._server_thread.daemon = True
        self._server_thread.start()

    def _start_loops(self):


        self._connect_thread = threading.Thread(target=self.ConnectToPeersLoop, name='LocalNode.AddTransactionLoop')
        self._connect_thread.daemon = True
        self._connect_thread.start()

        self._pool_thread = threading.Thread(target=self.AddTransactionLoop, name='LocalNode.AddTransactionLoop')
        self._pool_thread.daemon = True
        self._pool_thread.start()


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