import sys
import logging

# no logging for the node

# logname = 'nodes.log'
# logging.basicConfig(
#     level=logging.DEBUG,
#     filemode='a',
#     filename=logname,
#     format="%(levelname)s:%(name)s:%(funcName)s:%(message)s")


from neo.Network.NodeLeader import NodeLeader
from twisted.internet import reactor, task

from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Settings import settings


blockchain = LevelDBBlockchain(settings.LEVELDB_PATH)
Blockchain.RegisterBlockchain(blockchain)


dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
dbloop.start(.01)


NodeLeader.Instance().Start()

reactor.run()
