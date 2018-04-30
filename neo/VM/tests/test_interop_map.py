from unittest import TestCase
from neo.VM.InteropService import Integer, BigInteger, ByteArray, StackItem, Map, Array
from neo.VM.ExecutionEngine import ExecutionEngine
from neo.VM.ExecutionContext import ExecutionContext
from neo.VM import OpCode
from neo.VM import VMState
from mock import patch
from neo.Settings import settings
from logging import DEBUG


class StringIn(str):
    def __eq__(self, other):
        return self in other


class InteropTest(TestCase):
    engine = None
    econtext = None

    @classmethod
    def setUpClass(cls):
        super(InteropTest, cls).setUpClass()
        settings.set_loglevel(DEBUG)

    def setUp(self):
        self.engine = ExecutionEngine()
        self.econtext = ExecutionContext()

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
        self.engine.ExecuteOp(OpCode.NEWMAP, self.econtext)

        self.assertEqual(len(self.engine.EvaluationStack.Items), 1)
        self.assertIsInstance(self.engine.EvaluationStack.Items[0], Map)
        self.assertEqual(self.engine.EvaluationStack.Items[0].GetMap(), {})

    def test_op_map2(self):
        self.engine.ExecuteOp(OpCode.NEWMAP, self.econtext)
        self.engine.EvaluationStack.PushT(StackItem.New('mykey'))
        self.engine.EvaluationStack.PushT(StackItem.New('myVal'))
        self.engine.ExecuteOp(OpCode.SETITEM, self.econtext)

        self.assertEqual(len(self.engine.EvaluationStack.Items), 0)

    def test_op_map3(self):
        # set item should fail if not enough things on estack

        self.engine.EvaluationStack.PushT(StackItem.New('myvalue'))
        self.engine.EvaluationStack.PushT(StackItem.New('mykey'))

        with self.assertRaises(Exception) as context:
            self.engine.ExecuteOp(OpCode.SETITEM, self.econtext)

        self.assertEqual(len(self.engine.EvaluationStack.Items), 0)
        self.assertEqual(self.engine.State, VMState.BREAK)

    @patch('logzero.logger.error')
    def test_op_map4(self, mocked_logger):
        # set item should fail if these are out of order
        self.engine.EvaluationStack.PushT(StackItem.New('mykey'))
        self.engine.ExecuteOp(OpCode.NEWMAP, self.econtext)
        self.engine.EvaluationStack.PushT(StackItem.New('myVal'))
        self.engine.ExecuteOp(OpCode.SETITEM, self.econtext)

        self.assertEqual(self.engine.State, VMState.FAULT | VMState.BREAK)

        mocked_logger.assert_called_with(StringIn('VMFault.KEY_IS_COLLECTION'))

    @patch('logzero.logger.error')
    def test_op_map5(self, mocked_logger):
        # set item should fail if these are out of order
        self.engine.EvaluationStack.PushT(StackItem.New('mykey'))
        self.engine.EvaluationStack.PushT(StackItem.New('mykey'))
        self.engine.EvaluationStack.PushT(StackItem.New('myVal'))
        self.engine.ExecuteOp(OpCode.SETITEM, self.econtext)

        self.assertEqual(self.engine.State, VMState.FAULT | VMState.BREAK)

        mocked_logger.assert_called_with(StringIn('VMFault.SETITEM_INVALID_TYPE'))

    @patch('logzero.logger.error')
    def test_op_map6(self, mocked_logger):
        # we can pick an item from a dict
        self.engine.EvaluationStack.PushT(Map(dict={StackItem.New('a'): StackItem.New(4)}))
        self.engine.EvaluationStack.PushT(StackItem.New('a'))
        self.engine.ExecuteOp(OpCode.PICKITEM, self.econtext)

        self.assertEqual(len(self.engine.EvaluationStack.Items), 1)
        self.assertEqual(self.engine.EvaluationStack.Items[0].GetBigInteger(), 4)

    @patch('logzero.logger.error')
    def test_op_map7(self, mocked_logger):
        # pick item with key is collection causes error
        self.engine.EvaluationStack.PushT(Map(dict={StackItem.New('a'): StackItem.New(4)}))
        self.engine.EvaluationStack.PushT(Map(dict={StackItem.New('a'): StackItem.New(4)}))
        self.engine.ExecuteOp(OpCode.PICKITEM, self.econtext)

        self.assertEqual(self.engine.State, VMState.FAULT | VMState.BREAK)

        mocked_logger.assert_called_with(StringIn('VMFault.KEY_IS_COLLECTION'))

    @patch('logzero.logger.error')
    def test_op_map7(self, mocked_logger):
        # pick item on non collection causes error
        self.engine.EvaluationStack.PushT(StackItem.New('a'))
        self.engine.EvaluationStack.PushT(StackItem.New('a'))
        self.engine.ExecuteOp(OpCode.PICKITEM, self.econtext)

        self.assertEqual(self.engine.State, VMState.FAULT | VMState.BREAK)

        mocked_logger.assert_called_with(StringIn('Cannot access item at index') and StringIn('Item is not an array or dict'))

    @patch('logzero.logger.error')
    def test_op_map9(self, mocked_logger):
        # pick item key not found
        self.engine.EvaluationStack.PushT(Map(dict={StackItem.New('a'): StackItem.New(4)}))
        self.engine.EvaluationStack.PushT(StackItem.New('b'))
        self.engine.ExecuteOp(OpCode.PICKITEM, self.econtext)

        self.assertEqual(self.engine.State, VMState.FAULT | VMState.BREAK)

        mocked_logger.assert_called_with(StringIn('VMFault.DICT_KEY_NOT_FOUND'))

    def test_op_map10(self):
        # pick item key not found
        self.engine.EvaluationStack.PushT(Map(dict={StackItem.New('a'): StackItem.New(4), StackItem.New('b'): StackItem.New(5)}))
        self.engine.ExecuteOp(OpCode.KEYS, self.econtext)

        self.assertIsInstance(self.engine.EvaluationStack.Items[0], Array)
        items = self.engine.EvaluationStack.Items[0].GetArray()
        self.assertEqual(items, [StackItem.New('a'), StackItem.New('b')])

    def test_op_map11(self):
        self.engine.EvaluationStack.PushT(Map(dict={StackItem.New('a'): StackItem.New(4), StackItem.New('b'): StackItem.New(5)}))
        self.engine.ExecuteOp(OpCode.VALUES, self.econtext)

        self.assertIsInstance(self.engine.EvaluationStack.Items[0], Array)
        items = self.engine.EvaluationStack.Items[0].GetArray()
        self.assertEqual(items, [StackItem.New(4), StackItem.New(5)])

    def test_op_map12(self):
        self.engine.EvaluationStack.PushT(Map(dict={StackItem.New('a'): StackItem.New(4), StackItem.New('b'): StackItem.New(5)}))
        self.engine.EvaluationStack.PushT(StackItem.New('b'))
        self.engine.ExecuteOp(OpCode.HASKEY, self.econtext)

        self.assertEqual(self.engine.EvaluationStack.Items[0].GetBoolean(), True)

    def test_op_map13(self):
        self.engine.EvaluationStack.PushT(Map(dict={StackItem.New('a'): StackItem.New(4), StackItem.New('b'): StackItem.New(5)}))
        self.engine.EvaluationStack.PushT(StackItem.New('c'))
        self.engine.ExecuteOp(OpCode.HASKEY, self.econtext)

        self.assertEqual(self.engine.EvaluationStack.Items[0].GetBoolean(), False)
