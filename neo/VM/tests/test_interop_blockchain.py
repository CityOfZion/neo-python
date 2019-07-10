from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.VM.InteropService import StackItem
from neo.VM.ExecutionEngine import ExecutionEngine
from neo.VM.ExecutionContext import ExecutionContext
from neo.SmartContract.StateReader import StateReader
from neo.Core.Block import Block
from neo.Core.TX.Transaction import Transaction
from neo.Settings import settings
from neo.Core.UInt256 import UInt256
from neo.VM.Script import Script
import os
from neo.Blockchain import GetBlockchain
from neo.SmartContract import TriggerType


class StringIn(str):
    def __eq__(self, other):
        return self in other


class BlockchainInteropTest(BlockchainFixtureTestCase):
    engine = None
    econtext = None
    state_reader = None

    @classmethod
    def leveldb_testpath(cls):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    @classmethod
    def setUpClass(cls):
        super(BlockchainInteropTest, cls).setUpClass()

    def setUp(self):
        self.engine = ExecutionEngine()
        self.econtext = ExecutionContext(Script(self.engine.Crypto, b''), 0)
        self.engine.InvocationStack.PushT(self.econtext)
        snapshot = GetBlockchain()._db.createSnapshot()
        self.state_reader = StateReader(TriggerType.Application, snapshot)

    def test_interop_getblock(self):
        height = StackItem.New(9369)

        self.econtext.EvaluationStack.PushT(height)
        self.engine.InvocationStack.PushT(self.econtext)
        self.state_reader.Blockchain_GetBlock(self.engine)

        block = self.econtext.EvaluationStack.Pop().GetInterface()

        self.assertIsInstance(block, Block)

    def test_interop_get_transaction(self):
        u256 = UInt256.ParseString('8be9660512991d36e016b8ced6fda5d611d26a0f6e2faaaf1f379496edb3395f')

        hash = StackItem.New(u256.Data)

        self.econtext.EvaluationStack.PushT(hash)
        self.engine.InvocationStack.PushT(self.econtext)
        self.state_reader.Blockchain_GetTransaction(self.engine)

        tx = self.econtext.EvaluationStack.Pop().GetInterface()

        self.assertIsInstance(tx, Transaction)

    def test_interop_get_bad_transaction(self):
        u256 = UInt256.ParseString('8be9660512991d36e016b8ced6fda5d611d26a0f6e2faaaf1f379496edb33956')

        hash = StackItem.New(u256.Data)

        self.econtext.EvaluationStack.PushT(hash)
        self.engine.InvocationStack.PushT(self.econtext)
        self.state_reader.Blockchain_GetTransaction(self.engine)

        tx = self.econtext.EvaluationStack.Pop().GetInterface()

        self.assertIsNone(tx)

    def test_interop_get_transaction_height(self):
        u256 = UInt256.ParseString('8be9660512991d36e016b8ced6fda5d611d26a0f6e2faaaf1f379496edb3395f')

        hash = StackItem.New(u256.Data)

        self.econtext.EvaluationStack.PushT(hash)
        self.engine.InvocationStack.PushT(self.econtext)
        self.state_reader.Blockchain_GetTransactionHeight(self.engine)

        height = self.econtext.EvaluationStack.Pop().GetBigInteger()

        self.assertEqual(height, 9369)

    def test_interop_get_bad_transaction_height(self):
        u256 = UInt256.ParseString('8be9660512991d36e016b8ced6fda5d611d26a0f6e2faaaf1f379496edb33956')

        hash = StackItem.New(u256.Data)

        self.econtext.EvaluationStack.PushT(hash)
        self.engine.InvocationStack.PushT(self.econtext)
        self.state_reader.Blockchain_GetTransactionHeight(self.engine)

        height = self.econtext.EvaluationStack.Pop().GetBigInteger()

        self.assertEqual(height, -1)
