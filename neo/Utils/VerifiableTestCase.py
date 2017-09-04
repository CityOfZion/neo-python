from neo.Core.TX.RegisterTransaction import RegisterTransaction
from neo.Core.TX.MinerTransaction import MinerTransaction
from neo.Core.TX.IssueTransaction import IssueTransaction
from neo.Core.TX.Transaction import *
from neo.SmartContract.Contract import Contract
from neo.Core.Blockchain import Blockchain
from neo.Core.Helper import Helper
from neo.Core.Witness import Witness
from neo.VM.OpCode import *
from neo import Settings
from neo.Cryptography.Crypto import Crypto
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
import shutil

from neo.Utils.NeoTestCase import NeoTestCase

class VerifiableTestCase(NeoTestCase):

    LEVELDB_TESTPATH = './VerifiableUnitTest'

    _blockchain = None

    @classmethod
    def setUpClass(self):
        self._blockchain = LevelDBBlockchain(path=self.LEVELDB_TESTPATH)
        Blockchain.RegisterBlockchain(self._blockchain)

    @classmethod
    def tearDownClass(self):
        self._blockchain.Dispose()
        shutil.rmtree(self.LEVELDB_TESTPATH)
