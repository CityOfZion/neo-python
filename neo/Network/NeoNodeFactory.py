from twisted.internet.protocol import Protocol, Factory
from .NeoNode import NeoNode



from autologging import logged

@logged
class NeoFactory(Factory):


    def __init__(self):
        self.startFactory()

    def startFactory(self):
        pass

    def stopFactory(self):
        pass

    def buildProtocol(self, addr):
        from .NodeLeader import NodeLeader
        return NeoNode(self, NodeLeader.Instance())


