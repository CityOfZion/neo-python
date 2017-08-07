import sys
import logging
logname = 'nodes.log'
logging.basicConfig(
     level=logging.DEBUG,
     filemode='a',
     filename=logname,
     format="%(levelname)s:%(name)s:%(funcName)s:%(message)s")

from neo.Network.NeoNode import NeoNode
from neo.Network.NeoNodeFactory import NeoFactory

from twisted.internet.endpoints import TCP4ClientEndpoint,TCP4ServerEndpoint
from twisted.internet import reactor, defer

from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo import Settings

blockchain = LevelDBBlockchain(Settings.LEVELDB_PATH)
Blockchain.RegisterBlockchain(blockchain)

#endpoint = TCP4ServerEndpoint(reactor, 20333)
#endpoint.listen(NeoFactory())


from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

for bootstrap in Settings.SEED_LIST:
    host, port = bootstrap.split(":")
    point = TCP4ClientEndpoint(reactor, host, int(port))
    d = connectProtocol(point, NeoNode(NeoFactory))

print("Starting node ...")
reactor.run()