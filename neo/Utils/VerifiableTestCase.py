from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
import shutil
import time
from neo.Utils.NeoTestCase import NeoTestCase


class VerifiableTestCase(NeoTestCase):

    LEVELDB_TESTPATH = './fixtures/test_chain'

    _blockchain = None

    @classmethod
    def setUpClass(self):
        self._blockchain = LevelDBBlockchain(path=self.LEVELDB_TESTPATH)
        Blockchain.RegisterBlockchain(self._blockchain)

    @classmethod
    def tearDownClass(cls):
        cls._blockchain.Dispose()
        shutil.rmtree(cls.LEVELDB_TESTPATH)
