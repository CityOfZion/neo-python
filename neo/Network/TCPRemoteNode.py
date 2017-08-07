import socketserver
import socket
import threading
from .RemoteNode import RemoteNode
from .IPEndpoint import IPEndpoint
from .Message import Message
import asyncio
from neo.Core.Helper import Helper
from gevent import monkey
import binascii

from autologging import logged

monkey.patch_all()



class TCPListener(socketserver.ThreadingMixIn, socketserver.TCPServer):


    pass

@logged
class TCPRemoteNode(RemoteNode, socketserver.BaseRequestHandler):


    _socket = None
#    _stream = None
    _server = None
    _server_thread = None
    _connected = False
    __disposed = 0


    def ToString(self):
        return "TCP Remote Node: %s " % self.ListenerEndpoint.ToAddress()

    def __init__(self, localnode, remote_endpoint=None, sock=None, server_id=0):
        super(TCPRemoteNode, self).__init__(localnode)

        self.ListenerEndpoint = remote_endpoint
        self.ServerID = server_id

        if remote_endpoint:
            if remote_endpoint.Address == '0.0.0.0':
    #            self.__log.debug("has remote endpoint ANY")
                try:
                    self._server = TCPListener((remote_endpoint.Address, remote_endpoint.Port), TCPRemoteNode, True)
                    self._server.serve_forever()
                    self._socket = self._server.socket

                except Exception as e:
                    self.__log.debug("could not bind server: %s " % e)


            if not self._server:

                self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    def handle(self):
        try:

            message = Message.DeserializeFromAsyncSocket( self._socket, None)
            return message

        except Exception as e:
            self.__log.debug("could not receive message %s " % e)
            return None


    def ConnectAsync(self):

        try:
            self._socket.connect((self.ListenerEndpoint.Address, self.ListenerEndpoint.Port))
            return self.OnConnected()

        except Exception as e:
            self.__log.debug("could not connect async: %s " % e)

            self.Disconnect(False)

        return False



    def Disconnect(self, error):

        if self.__disposed == 0 and self._server:
            self._server.shutdown()
            self._socket.close()

            super(TCPRemoteNode, self).Disconnect(error)


    async def ReceiveMessageAsync(self, timeout):

        try:

            message = Message.DeserializeFromAsyncSocket(self._socket, None)
            return message
        except Exception as e:
            self.__log.debug("could not receive message async: %s " % e)

        return None

    def AcceptSocketAsync(self):
        sock, addr = self._socket.accept()
        return sock,addr

    async def SendMessageAsync(self, message):
#        self.__log.debug("Remote Node Sending message async- Command: %s %s" % (message.Command, message.Payload))
        if not self._connected or self.__disposed > 0: return False

        ba = Helper.ToArray(message)

        ba2 = binascii.unhexlify( ba)
        try:
            self._socket.sendall(ba2)
            return True
        except Exception as e:
            self.__log.debug("could not send message %s " % e)

        return False

    def OnConnected(self):
        self.RemoteEndpoint = self.ListenerEndpoint
        self._connected = True

        return True

