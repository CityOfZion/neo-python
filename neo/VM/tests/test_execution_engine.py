from unittest import TestCase
from neo.VM.InteropService import *
from neo.VM.ExecutionEngine import ExecutionEngine
from neo.VM.ExecutionEngine import ExecutionContext
from neo.VM import OpCode


class VMTestCase(TestCase):

    engine = None
    econtext = None

    def setUp(self):

        self.engine = ExecutionEngine()
        self.econtext = ExecutionContext()

    def test_add_operations(self):

        self.engine.EvaluationStack.PushT(StackItem.New(2))
        self.engine.EvaluationStack.PushT(StackItem.New(3))

        self.engine.ExecuteOp(OpCode.ADD, self.econtext)

        self.assertEqual(len(self.engine.EvaluationStack.Items), 1)

        self.assertEqual(self.engine.EvaluationStack.Items[0], StackItem.New(5))

    def test_sub_operations(self):

        self.engine.EvaluationStack.PushT(StackItem.New(2))
        self.engine.EvaluationStack.PushT(StackItem.New(3))

        self.engine.ExecuteOp(OpCode.SUB, self.econtext)

        self.assertEqual(len(self.engine.EvaluationStack.Items), 1)

        self.assertEqual(self.engine.EvaluationStack.Items[0], StackItem.New(-1))
