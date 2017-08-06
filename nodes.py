from neo.Network.NeoNode import NeoNode
from neo.Network.NeoNodeFactory import NeoFactory

from twisted.internet.endpoints import TCP4ClientEndpoint,TCP4ServerEndpoint
from twisted.internet import reactor

from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo import Settings

blockchain = LevelDBBlockchain(Settings.LEVELDB_PATH)
Blockchain.RegisterBlockchain(blockchain)

endpoint = TCP4ServerEndpoint(reactor, 20333)
endpoint.listen(NeoFactory())


from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

def gotProtocol(p):
    """The callback to start the protocol exchange. We let connecting
    nodes start the hello handshake"""
    p.send_hello()


#point = TCP4ClientEndpoint(reactor, "localhost", 20333)
#d = connectProtocol(point, NeoProtocol)
#d.addCallback(gotProtocol)

BOOTSTRAP_LIST = ["seed1.neo.org:20333",]

for bootstrap in BOOTSTRAP_LIST:
    host, port = bootstrap.split(":")
    point = TCP4ClientEndpoint(reactor, host, int(port))
    d = connectProtocol(point, NeoNode(NeoFactory))
    d.addCallback(gotProtocol)

reactor.run()