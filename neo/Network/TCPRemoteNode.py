import socketserver
import socket
import threading
from .RemoteNode import RemoteNode
from .IPEndpoint import IPEndpoint
from .Message import Message
import asyncio
from neo.Core.Helper import Helper
from gevent import monkey

monkey.patch_all()


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


    pass

class TCPRemoteNode(RemoteNode, socketserver.BaseRequestHandler):


    _socket = None
#    _stream = None
    _server = None
    _server_thread = None
    _connected = False
    __disposed = 0

    def ToString(self):
        return "TCP Remote Node: %s " % self.ListenerEndpoint.ToAddress()

    def __init__(self, localnode, remote_endpoint=None, sock=None):
        super(TCPRemoteNode, self).__init__(localnode)

        self.ListenerEndpoint = remote_endpoint

        if remote_endpoint:
            if remote_endpoint.Address == '0.0.0.0':
    #            print("has remote endpoint ANY")
                try:
                    self._server = TCPListener((remote_endpoint.Address, remote_endpoint.Port), TCPRemoteNode, True)
                    self._server.serve_forever()
                    self._socket = self._server.socket
                    print("created server: %s " % self._server)

                except Exception as e:
                    print("could not bind server: %s " % e)


            if not self._server:

                self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)



    def handle(self):
#        print("handle tcp request:  %s " % self.request)
#        print("address is : %s " % self.client_address)
#        print("server: %s " % self.server)

        #data = str(self.request.recv(1024), 'ascii')
        #cur_thread = threading.current_thread()
        #response = bytes("{}: {}".format(cur_thread.name, data), 'ascii')
        #self.request.sendall(response)
        try:

            message = Message.DeserializeFromAsyncSocket( self._socket, None)
            return message

        except Exception as e:
            print("could not receive message %s " % e)
            return None


    def ConnectAsync(self):
        print("remote node connect async::")

        try:

            self._socket.connect((self.ListenerEndpoint.Address, self.ListenerEndpoint.Port))
            return self.OnConnected()

        except Exception as e:
            print("could not connect async: %s " % e)

            self.Disconnect(False)

        return False



    def Disconnect(self, error):

        if self.__disposed == 0 and self._server:
            self._server.shutdown()

            super(TCPRemoteNode, self).Disconnect(error)


    async def ReceiveMessageAsync(self, timeout):

        try:

            message = Message.DeserializeFromAsyncSocket(self._socket, None)
            return message
        except Exception as e:
            print("could not receive message async: %s " % e)

        return None

    def AcceptSocketAsync(self):
        sock, addr = self._socket.accept()
        print("accept socket async: %s %s  " % (sock, addr))
        return sock,addr

    async def SendMessageAsync(self, message):
        print("remote node send message async: :%s " % message)
        if not self._connected or self.__disposed > 0: return False

        ba = Helper.ToArray(message)

        try:
            self._socket.send(ba)
            return True
        except Exception as e:
            print("could not send message %s " % e)

        return False

    def OnConnected(self):
        print("Remote node on connected...")
#        addr = self._socket.gethostname()
#        addr = socket.gethostname()
#        print("addrs::: %s " % addr)
#        self.RemoteEndpoint = IPEndpoint(addr.split(':')[0], addr.split(':')[1])
        self.RemoteEndpoint = self.ListenerEndpoint
        self._connected = True

        return True

