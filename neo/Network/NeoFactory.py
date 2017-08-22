from twisted.internet.protocol import ReconnectingClientFactory
from neo.Network.NeoNode import NeoNode


class NeoFactory(ReconnectingClientFactory):


    def buildProtocol(self, addr):
        return NeoNode(self)


