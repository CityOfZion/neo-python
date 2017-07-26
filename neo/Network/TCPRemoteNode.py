import socketserver
import socket
import threading
from .RemoteNode import RemoteNode
from .IPEndpoint import IPEndpoint
from .Message import Message
import asyncio
from neo.Core.Helper import Helper
class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        print("handle tcp request:  %s " % self.request)
        print("address is : %s " % self.client_address)
        print("server: %s " % self.server)

        data = str(self.request.recv(1024), 'ascii')
        cur_thread = threading.current_thread()
        response = bytes("{}: {}".format(cur_thread.name, data), 'ascii')
        self.request.sendall(response)



class TCPListener(socketserver.ThreadingMixIn, socketserver.TCPServer):


    def AcceptSocketsAsync(self):
        self.socket.accept()


class TCPRemoteNode(RemoteNode, socketserver.BaseRequestHandler):


#    _socket = None
#    _stream = None
    _server = None
    _server_thread = None
    _connected = False
    __disposed = 0

    def __init__(self, localnode, remote_endpoint=None, sock=None):
        super(TCPRemoteNode, self).__init__(localnode)


        if remote_endpoint:


            self._server = TCPListener((remote_endpoint.Address, remote_endpoint.Port), TCPRemoteNode, True)

            self.ListenerEndpoint = remote_endpoint

            self._server_thread = threading.Thread(target= self._server.serve_forever())
            self._server_thread.daemon = True
            self._server_thread.start()

        elif sock:

            hostname = sock.gethostname()
            self._server = TCPListener((IPEndpoint.ANY, 0), TCPRemoteNode, True)
            self._server.socket = sock
            self.OnConnected()


    def handle(self):
        print("handle tcp request:  %s " % self.request)
        print("address is : %s " % self.client_address)
        print("server: %s " % self.server)

        #data = str(self.request.recv(1024), 'ascii')
        #cur_thread = threading.current_thread()
        #response = bytes("{}: {}".format(cur_thread.name, data), 'ascii')
        #self.request.sendall(response)
        try:

            buffer = bytearray()
            return Message.DeserializeFromAsyncSocket( self.server.socket, None)

        except Exception as e:
            print("could not receive message")
            return None


    async def ConnectAsync(self):
        address = self.ListenerEndpoint.Address

        try:

            self._server.socket.connect(address, self.ListenerEndpoint.Port)
            self.OnConnected()

        except Exception as e:
            print("could not connect async: %s " % e)

            self.Disconnect(False)
            return False

        return True


    def Disconnect(self, error):

        if self.__disposed == 0:
            self.server.shutdown()

            super(TCPRemoteNode, self).Disconnect(error)



    def ReceiveMessageAsync(self, timeout):
        #this is handled by the handle method
        pass




    async def SendMessageAsync(self, message):

        if not self._connected or self.__disposed > 0: return False

        ba = Helper.ToArray(message)

        try:
            self._server.socket.send(ba)
            return True
        except Exception as e:
            print("could not send message %s " % e)

        return False

    def OnConnected(self):
        addr = self._server.socket.gethostname()
        self.RemoteEndpoint = IPEndpoint(addr.split(':')[0], addr.split(':')[1])
        self._connected = True
