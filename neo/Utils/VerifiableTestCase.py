from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
import shutil
from neo.Utils.NeoTestCase import NeoTestCase
from neo.Settings import settings
import os


class VerifiableTestCase(NeoTestCase):

    LEVELDB_TESTPATH = os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    _blockchain = None

    @classmethod
    def setUpClass(self):
        os.makedirs(self.LEVELDB_TESTPATH, exist_ok=True)
        self._blockchain = LevelDBBlockchain(path=self.LEVELDB_TESTPATH, skip_version_check=True)
        Blockchain.RegisterBlockchain(self._blockchain)

    @classmethod
    def tearDownClass(cls):
        cls._blockchain.Dispose()
        shutil.rmtree(cls.LEVELDB_TESTPATH)
