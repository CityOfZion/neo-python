from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Core.Blockchain import Blockchain
from neo import Settings
from neo.Network.LocalNode import LocalNode

class CLI(object):

    __instance__=None

    _blockchain = None
    _wallet = None
    _localnode = None

    def __init__(self):

        self._blockchain = LevelDBBlockchain( Settings.LEVELDB_PATH )
        Blockchain.RegisterBlockchain(self._blockchain)
        self._localnode = LocalNode()
        self.start_node()

    async def start_node(self):

        await self._localnode.Start(20333, 20334)


    def SetWallet(self, wallet):
        self._wallet = wallet

    def GetWallet(self):
        return self._wallet

    @staticmethod
    def Instance():
        if not CLI.__instance__:
            CLI.__instance__ = CLI()
        return CLI.__instance__

    @staticmethod
    def OpenWallet(path, password, create):
        CLI.Instance().SetWallet(  UserWallet(path, password, create))
        return CLI.Instance().GetWallet()

