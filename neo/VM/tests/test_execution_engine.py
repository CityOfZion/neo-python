from unittest import TestCase
from neo.VM.InteropService import StackItem, ByteArray
from neo.VM.ExecutionEngine import ExecutionEngine
from neo.VM.ExecutionEngine import ExecutionContext
from neo.VM import OpCode
from neocore.Cryptography.Crypto import Crypto
from mock import patch
import binascii
from neo.Core.TX.Transaction import ContractTransaction


class VMTestCase(TestCase):
    engine = None
    econtext = None

    def setUp(self):
        self.engine = ExecutionEngine(crypto=Crypto.Default())
        self.econtext = ExecutionContext(engine=self.engine)

    def test_add_operations(self):
        self.econtext.EvaluationStack.PushT(StackItem.New(2))
        self.econtext.EvaluationStack.PushT(StackItem.New(3))

        self.engine.ExecuteOp(OpCode.ADD, self.econtext)

        self.assertEqual(len(self.econtext.EvaluationStack.Items), 1)

        self.assertEqual(self.econtext.EvaluationStack.Items[0], StackItem.New(5))

    def test_sub_operations(self):
        self.econtext.EvaluationStack.PushT(StackItem.New(2))
        self.econtext.EvaluationStack.PushT(StackItem.New(3))

        self.engine.ExecuteOp(OpCode.SUB, self.econtext)

        self.assertEqual(len(self.econtext.EvaluationStack.Items), 1)

        self.assertEqual(self.econtext.EvaluationStack.Items[0], StackItem.New(-1))

    def test_verify_sig(self):
        stackItemMessage = ByteArray('abcdef')
        self.econtext.EvaluationStack.PushT(stackItemMessage)

        # sig
        sig = binascii.unhexlify(b'cd0ca967d11cea78e25ad16f15dbe77672258bfec59ff3617c95e317acff063a48d35f71aa5ce7d735977412186e1572507d0f4d204c5bcb6c90e03b8b857fbd')
        self.econtext.EvaluationStack.PushT(StackItem.New(sig))

        # pubkey
        pubkey = binascii.unhexlify(b'036fbcb5e138c1ce5360e861674c03228af735a9114a5b7fb4121b8350129f3ffe')
        self.econtext.EvaluationStack.PushT(pubkey)

        self.engine.ExecuteOp(OpCode.VERIFY, self.econtext)

        res = self.econtext.EvaluationStack.Pop()
        self.assertEqual(res, StackItem.New(True))

    def test_verify_sig_fail(self):
        # push message ( should be hexlified )
        stackItemMessage = ByteArray('abcdefg')
        self.econtext.EvaluationStack.PushT(stackItemMessage)

        # sig
        sig = binascii.unhexlify(b'cd0ca967d11cea78e25ad16f15dbe77672258bfec59ff3617c95e317acff063a48d35f71aa5ce7d735977412186e1572507d0f4d204c5bcb6c90e03b8b857fbd')
        self.econtext.EvaluationStack.PushT(StackItem.New(sig))

        # pubkey
        pubkey = binascii.unhexlify(b'036fbcb5e138c1ce5360e861674c03228af735a9114a5b7fb4121b8350129f3ffd')
        self.econtext.EvaluationStack.PushT(pubkey)

        self.engine.ExecuteOp(OpCode.VERIFY, self.econtext)

        res = self.econtext.EvaluationStack.Pop()
        self.assertEqual(res, StackItem.New(False))
