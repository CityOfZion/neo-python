from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.VM.InteropService import Integer, BigInteger, ByteArray, StackItem, Map, Array
from neo.VM.ExecutionEngine import ExecutionEngine
from neo.VM.ExecutionContext import ExecutionContext
from neo.SmartContract.StateReader import StateReader
from neo.Core.Block import Block
from neo.Core.TX.Transaction import Transaction
from neo.Settings import settings
from logging import DEBUG
from neocore.UInt256 import UInt256
import os


class StringIn(str):
    def __eq__(self, other):
        return self in other


class BlockchainInteropTest(BlockchainFixtureTestCase):
    engine = None
    econtext = None
    state_reader = None

    @classmethod
    def leveldb_testpath(self):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    @classmethod
    def setUpClass(cls):
        super(BlockchainInteropTest, cls).setUpClass()
        settings.set_loglevel(DEBUG)

    def setUp(self):
        self.engine = ExecutionEngine()
        self.econtext = ExecutionContext()
        self.state_reader = StateReader()

    def test_interop_getblock(self):

        height = StackItem.New(1234)

        self.engine.EvaluationStack.PushT(height)
        self.state_reader.Blockchain_GetBlock(self.engine)

        block = self.engine.EvaluationStack.Pop().GetInterface()

        self.assertIsInstance(block, Block)

    def test_interop_get_transaction(self):

        u256 = UInt256.ParseString('e4d2ea5df2adf77df91049beccbb16f98863b93a16439c60381eac1f23bff178')

        hash = StackItem.New(u256.Data)

        self.engine.EvaluationStack.PushT(hash)
        self.state_reader.Blockchain_GetTransaction(self.engine)

        tx = self.engine.EvaluationStack.Pop().GetInterface()

        self.assertIsInstance(tx, Transaction)

    def test_interop_get_bad_transaction(self):

        u256 = UInt256.ParseString('e4d2ea5df2adf77df91049beccbb16f98863b93a16439c60381eac1f23bff176')

        hash = StackItem.New(u256.Data)

        self.engine.EvaluationStack.PushT(hash)
        self.state_reader.Blockchain_GetTransaction(self.engine)

        tx = self.engine.EvaluationStack.Pop().GetInterface()

        self.assertIsNone(tx)

    def test_interop_get_transaction_height(self):

        u256 = UInt256.ParseString('e4d2ea5df2adf77df91049beccbb16f98863b93a16439c60381eac1f23bff178')

        hash = StackItem.New(u256.Data)

        self.engine.EvaluationStack.PushT(hash)
        self.state_reader.Blockchain_GetTransactionHeight(self.engine)

        height = self.engine.EvaluationStack.Pop().GetBigInteger()

        self.assertEqual(height, 4999)

    def test_interop_get_bad_transaction_height(self):

        u256 = UInt256.ParseString('e4d2ea5df2adf77df91049beccbb16f98863b93a16439c60381eac1f23bff176')

        hash = StackItem.New(u256.Data)

        self.engine.EvaluationStack.PushT(hash)
        self.state_reader.Blockchain_GetTransactionHeight(self.engine)

        height = self.engine.EvaluationStack.Pop().GetBigInteger()

        self.assertEqual(height, -1)
