from twisted.internet.protocol import ReconnectingClientFactory
from neo.Network.NeoNode import NeoNode
from autologging import logged

@logged
class NeoFactory(ReconnectingClientFactory):


    __connector = None
    __protocol = NeoNode

    def __init__(self, *args, **kwargs):
        super(NeoFactory, self).__init__(*args, **kwargs)

    def startFactory(self):
        super(NeoFactory, self).startFactory()

    def startedConnecting(self, connector):
        self.__connector = connector
        super(NeoFactory, self).startedConnecting(connector)

    def buildProtocol(self, addr):
        return self.__protocol()




#    def clientConnectionFailed(self, connector, reason):
#        print("client connection failed!!! %s %s" % (connector,reason))

    def clientConnectionLost(self, connector, unused_reason):
        self.__log.debug("client connection lost! %s %s " % (connector,unused_reason))
        super(NeoFactory,self).clientConnectionLost(connector,unused_reason)