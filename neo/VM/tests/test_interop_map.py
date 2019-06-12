from neo.Utils.NeoTestCase import NeoTestCase
from neo.VM.InteropService import Integer, BigInteger, ByteArray, StackItem, Map, Array
from neo.VM.ExecutionEngine import ExecutionEngine
from neo.VM.ExecutionContext import ExecutionContext
from neo.VM import OpCode
from neo.VM import VMState
from neo.VM.Script import Script
import logging


class StringIn(str):
    def __eq__(self, other):
        return self in other


class InteropTest(NeoTestCase):
    engine = None
    econtext = None

    @classmethod
    def setUpClass(cls):
        super(InteropTest, cls).setUpClass()

    def setUp(self):
        self.engine = ExecutionEngine()
        self.econtext = ExecutionContext(Script(self.engine.Crypto, b''), 0)
        self.engine.InvocationStack.PushT(self.econtext)

    def test_interop_map1(self):
        map = Map()

        self.assertEqual(map.Keys, [])
        self.assertEqual(map.Values, [])

        map.SetItem(Integer(BigInteger(3)), ByteArray(b'abc'))

        self.assertEqual(map.Keys, [Integer(BigInteger(3))])
        self.assertEqual(map.Values, [ByteArray(b'abc')])

    def test_interop_map2(self):
        map = Map({'a': 1, 'b': 2, 'c': 3})

        self.assertEqual(map.Count, 3)
        self.assertEqual(map.ContainsKey('a'), True)
        self.assertEqual(map.Contains('a'), False)

        map.Clear()

        self.assertEqual(map.GetMap(), {})

    def test_interop_map3(self):
        map = Map({'a': 1, 'b': 2, 'c': 3})

        self.assertEqual(map.GetBoolean(), True)

        with self.assertRaises(Exception) as context:
            map.GetByteArray()

        with self.assertRaises(Exception) as context:
            map.GetBigInteger()

        map2 = Map({'a': 1, 'b': 2, 'c': 3})

        self.assertEqual(map, map2)
        self.assertTrue(map.Remove('a'), True)
        self.assertEqual(map.Count, 2)
        self.assertNotEqual(map, map2)
        self.assertEqual(map.TryGetValue('b'), (True, 2))
        self.assertEqual(map.TryGetValue('h'), (False, None))

        map.SetItem('h', 9)

        self.assertEqual(map.GetItem('h'), 9)
        self.assertEqual(map.GetMap(), {'b': 2, 'c': 3, 'h': 9})

    def test_op_map1(self):
        self.econtext.Script._value = OpCode.NEWMAP
        self.engine.ExecuteInstruction()

        self.assertEqual(len(self.econtext.EvaluationStack.Items), 1)
        self.assertIsInstance(self.econtext.EvaluationStack.Items[0], Map)
        self.assertEqual(self.econtext.EvaluationStack.Items[0].GetMap(), {})

    def test_op_map2(self):
        self.econtext.Script._value = OpCode.NEWMAP + OpCode.SETITEM
        self.engine.ExecuteInstruction()

        self.econtext.EvaluationStack.PushT(StackItem.New('mykey'))
        self.econtext.EvaluationStack.PushT(StackItem.New('myVal'))
        self.engine.ExecuteInstruction()

        self.assertEqual(len(self.econtext.EvaluationStack.Items), 0)

    def test_op_map3(self):
        # set item should fail if not enough things on estack

        self.econtext.EvaluationStack.PushT(StackItem.New('myvalue'))
        self.econtext.EvaluationStack.PushT(StackItem.New('mykey'))
        self.econtext.Script._value = OpCode.SETITEM

        with self.assertRaises(Exception) as context:
            self.engine.ExecuteInstruction()

        self.assertEqual(len(self.econtext.EvaluationStack.Items), 0)
        self.assertEqual(self.engine.State, VMState.BREAK)

    def test_op_map4(self):
        with self.assertLogHandler('vm', logging.DEBUG) as log_context:
            # set item should fail if these are out of order
            self.econtext.Script._value = OpCode.NEWMAP + OpCode.SETITEM

            self.econtext.EvaluationStack.PushT(StackItem.New('mykey'))
            self.engine.ExecuteInstruction()
            self.econtext.EvaluationStack.PushT(StackItem.New('myVal'))
            self.engine.ExecuteInstruction()

            self.assertEqual(self.engine.State, VMState.FAULT)
            self.assertTrue(len(log_context.output) > 0)
            self.assertTrue('VMFault.KEY_IS_COLLECTION' in log_context.output[0])

    def test_op_map5(self):
        # need to set vm logging level to DEBUG or we will immediately exit `VM_FAULT_and_report()`
        with self.assertLogHandler('vm', logging.DEBUG) as log_context:
            # set item should fail if these are out of order
            self.econtext.EvaluationStack.PushT(StackItem.New('mykey'))
            self.econtext.EvaluationStack.PushT(StackItem.New('mykey'))
            self.econtext.EvaluationStack.PushT(StackItem.New('myVal'))
            self.econtext.Script._value = OpCode.SETITEM
            self.engine.ExecuteInstruction()

            self.assertEqual(self.engine.State, VMState.FAULT)

            self.assertTrue(len(log_context.output) > 0)
            self.assertEqual(log_context.records[0].levelname, 'DEBUG')
            self.assertTrue('VMFault.SETITEM_INVALID_TYPE' in log_context.output[0])

    def test_op_map6(self):
        # we can pick an item from a dict
        self.econtext.EvaluationStack.PushT(Map(dict={StackItem.New('a'): StackItem.New(4)}))
        self.econtext.EvaluationStack.PushT(StackItem.New('a'))
        self.econtext.Script._value = OpCode.PICKITEM
        self.engine.ExecuteInstruction()

        self.assertEqual(len(self.econtext.EvaluationStack.Items), 1)
        self.assertEqual(self.econtext.EvaluationStack.Items[0].GetBigInteger(), 4)

    def test_op_map7(self):
        with self.assertLogHandler('vm', logging.DEBUG) as log_context:
            # pick item with key is collection causes error
            self.econtext.EvaluationStack.PushT(Map(dict={StackItem.New('a'): StackItem.New(4)}))
            self.econtext.EvaluationStack.PushT(Map(dict={StackItem.New('a'): StackItem.New(4)}))
            self.econtext.Script._value = OpCode.PICKITEM
            self.engine.ExecuteInstruction()

            self.assertEqual(self.engine.State, VMState.FAULT)
            self.assertTrue(len(log_context.output) > 0)
            self.assertTrue('VMFault.KEY_IS_COLLECTION' in log_context.output[0])

    def test_op_map9(self):
        with self.assertLogHandler('vm', logging.DEBUG) as log_context:
            # pick item key not found
            self.econtext.EvaluationStack.PushT(Map(dict={StackItem.New('a'): StackItem.New(4)}))
            self.econtext.EvaluationStack.PushT(StackItem.New('b'))
            self.econtext.Script._value = OpCode.PICKITEM
            self.engine.ExecuteInstruction()

            self.assertEqual(self.engine.State, VMState.FAULT)
            self.assertTrue(len(log_context.output) > 0)
            self.assertTrue('VMFault.DICT_KEY_NOT_FOUND' in log_context.output[0])

    def test_op_map10(self):
        # pick item key not found
        self.econtext.EvaluationStack.PushT(Map(dict={StackItem.New('a'): StackItem.New(4), StackItem.New('b'): StackItem.New(5)}))
        self.econtext.Script._value = OpCode.KEYS
        self.engine.ExecuteInstruction()

        self.assertIsInstance(self.econtext.EvaluationStack.Items[0], Array)
        items = self.econtext.EvaluationStack.Items[0].GetArray()
        self.assertEqual(items, [StackItem.New('a'), StackItem.New('b')])

    def test_op_map11(self):
        self.econtext.EvaluationStack.PushT(Map(dict={StackItem.New('a'): StackItem.New(4), StackItem.New('b'): StackItem.New(5)}))
        self.econtext.Script._value = OpCode.VALUES
        self.engine.ExecuteInstruction()

        self.assertIsInstance(self.econtext.EvaluationStack.Items[0], Array)
        items = self.econtext.EvaluationStack.Items[0].GetArray()
        self.assertEqual(items, [StackItem.New(4), StackItem.New(5)])

    def test_op_map12(self):
        self.econtext.EvaluationStack.PushT(Map(dict={StackItem.New('a'): StackItem.New(4), StackItem.New('b'): StackItem.New(5)}))
        self.econtext.EvaluationStack.PushT(StackItem.New('b'))
        self.econtext.Script._value = OpCode.HASKEY
        self.engine.ExecuteInstruction()

        self.assertEqual(self.econtext.EvaluationStack.Items[0].GetBoolean(), True)

    def test_op_map13(self):
        self.econtext.EvaluationStack.PushT(Map(dict={StackItem.New('a'): StackItem.New(4), StackItem.New('b'): StackItem.New(5)}))
        self.econtext.EvaluationStack.PushT(StackItem.New('c'))
        self.econtext.Script._value = OpCode.HASKEY
        self.engine.ExecuteInstruction()

        self.assertEqual(self.econtext.EvaluationStack.Items[0].GetBoolean(), False)
