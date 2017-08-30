import sys
import logging

#no logging for the node

#logname = 'nodes.log'
#logging.basicConfig(
#     level=logging.DEBUG,
#     filemode='a',
#     filename=logname,
#     format="%(levelname)s:%(name)s:%(funcName)s:%(message)s")


from neo.Network.NodeLeader import NodeLeader
from twisted.internet import reactor, task

from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo import Settings


blockchain = LevelDBBlockchain(Settings.LEVELDB_PATH)
Blockchain.RegisterBlockchain(blockchain)



from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
dbloop.start(.01)

#for bootstrap in Settings.SEED_LIST:
#    host, port = bootstrap.split(":")
#    point = TCP4ClientEndpoint(reactor, host, int(port))
#    d = connectProtocol(point, NeoNode(NeoFactory))

NodeLeader.Instance().Start()

reactor.run()