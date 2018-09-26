from unittest import TestCase
from neo.VM.InteropService import Struct, StackItem, Array, Boolean, Map
from neo.VM.ExecutionEngine import ExecutionEngine
from neo.VM.ExecutionEngine import ExecutionContext
from neo.SmartContract.StateReader import StateReader
from neo.SmartContract.Iterable import Iterator, KeysWrapper, ValuesWrapper
from neo.SmartContract.Iterable.Wrapper import ArrayWrapper, MapWrapper
from neo.SmartContract.Iterable.ConcatenatedEnumerator import ConcatenatedEnumerator


class InteropSerializeDeserializeTestCase(TestCase):
    engine = None
    econtext = None
    state_reader = None

    def setUp(self):
        self.engine = ExecutionEngine()
        self.econtext = ExecutionContext(engine=self.engine)
        self.state_reader = StateReader()

    def test_iter_array(self):
        my_array = Array([StackItem.New(12),
                          StackItem.New(b'Hello World'),
                          StackItem.New(True),
                          Array([StackItem.New(113442), StackItem.New(2), StackItem.New(3)])
                          ])
        self.econtext.EvaluationStack.PushT(my_array)
        self.engine.InvocationStack.PushT(self.econtext)
        self.state_reader.Enumerator_Create(self.engine)

        iterable = self.econtext.EvaluationStack.Peek(0).GetInterface()

        self.assertIsInstance(iterable, ArrayWrapper)

        keys = []
        values = []
        while iterable.Next():
            currentKey = iterable.Key()
            keys.append(currentKey.GetBigInteger())
            values.append(iterable.Value())

        self.assertEqual(keys, [0, 1, 2, 3])
        self.assertEqual(values, my_array.GetArray())

    def test_iter_map(self):
        my_map = Map(
            {
                StackItem.New('a'): StackItem.New(1),
                StackItem.New('b'): StackItem.New(3),
                StackItem.New('d'): StackItem.New(432)
            }
        )

        self.econtext.EvaluationStack.PushT(my_map)
        self.engine.InvocationStack.PushT(self.econtext)

        self.state_reader.Iterator_Create(self.engine)

        iterable = self.econtext.EvaluationStack.Peek(0).GetInterface()

        self.assertIsInstance(iterable, MapWrapper)

        keys = []
        values = []
        while iterable.Next():
            keys.append(iterable.Key())
            values.append(iterable.Value())

        self.assertEqual(keys, [StackItem.New('a'), StackItem.New('b'), StackItem.New('d')])
        self.assertEqual(keys, my_map.Keys)

        self.assertEqual(values, [StackItem.New(1), StackItem.New(3), StackItem.New(432)])
        self.assertEqual(values, my_map.Values)

    def test_iter_array_keys(self):
        my_array = Array([StackItem.New(12),
                          StackItem.New(b'Hello World'),
                          StackItem.New(True),
                          Array([StackItem.New(113442), StackItem.New(2), StackItem.New(3)])
                          ])
        self.econtext.EvaluationStack.PushT(my_array)
        self.engine.InvocationStack.PushT(self.econtext)
        self.state_reader.Enumerator_Create(self.engine)

        create_iterkeys = self.state_reader.Iterator_Keys(self.engine)

        self.assertEqual(create_iterkeys, True)

        iterkeys = self.econtext.EvaluationStack.Peek(0).GetInterface()

        self.assertIsInstance(iterkeys, KeysWrapper)

        keys = []
        while iterkeys.Next():
            keys.append(iterkeys.Value().GetBigInteger())

        self.assertEqual(keys, [0, 1, 2, 3])

    def test_iter_array_values(self):
        my_array = Array([StackItem.New(12),
                          StackItem.New(b'Hello World'),
                          StackItem.New(True),
                          Array([StackItem.New(113442), StackItem.New(2), StackItem.New(3)])
                          ])
        self.econtext.EvaluationStack.PushT(my_array)
        self.engine.InvocationStack.PushT(self.econtext)
        self.state_reader.Enumerator_Create(self.engine)

        create_itervalues = self.state_reader.Iterator_Values(self.engine)

        self.assertEqual(create_itervalues, True)

        itervals = self.econtext.EvaluationStack.Peek(0).GetInterface()

        self.assertIsInstance(itervals, ValuesWrapper)

        values = []
        while itervals.Next():
            values.append(itervals.Value())

        self.assertEqual(values, my_array.GetArray())

    def test_iter_concat(self):
        my_array = Array([StackItem.New(12),
                          StackItem.New(b'Hello World'),
                          StackItem.New(True),
                          Array([StackItem.New(113442), StackItem.New(2), StackItem.New(3)])
                          ])

        my_array2 = Array([StackItem.New(b'a'), StackItem.New(b'b'), StackItem.New(4), StackItem.New(100)])

        self.econtext.EvaluationStack.PushT(my_array2)
        self.engine.InvocationStack.PushT(self.econtext)
        self.state_reader.Enumerator_Create(self.engine)

        self.econtext.EvaluationStack.PushT(my_array)

        self.state_reader.Enumerator_Create(self.engine)

        result = self.state_reader.Enumerator_Concat(self.engine)

        self.assertEqual(result, True)

        concatted_enum = self.econtext.EvaluationStack.Peek().GetInterface()

        self.assertIsInstance(concatted_enum, ConcatenatedEnumerator)

        values = []
        count = 0

        while concatted_enum.Next():
            count += 1
            values.append(concatted_enum.Value())

        self.assertEqual(count, 8)
        self.assertEqual(values, my_array.GetArray() + my_array2.GetArray())

    def test_iter_array_bad(self):
        my_item = StackItem.New(12)
        self.econtext.EvaluationStack.PushT(my_item)
        self.engine.InvocationStack.PushT(self.econtext)

        result = self.state_reader.Enumerator_Create(self.engine)

        self.assertEqual(result, False)
        self.assertEqual(self.econtext.EvaluationStack.Count, 0)

    def test_iter_map_bad(self):
        my_item = StackItem.New(12)
        self.econtext.EvaluationStack.PushT(my_item)
        self.engine.InvocationStack.PushT(self.econtext)
        result = self.state_reader.Iterator_Create(self.engine)

        self.assertEqual(result, False)
        self.assertEqual(self.econtext.EvaluationStack.Count, 0)

    def test_iter_array_key_bad(self):
        my_item = StackItem.New(12)
        self.econtext.EvaluationStack.PushT(my_item)
        self.engine.InvocationStack.PushT(self.econtext)

        result = self.state_reader.Iterator_Key(self.engine)

        self.assertEqual(result, False)
        self.assertEqual(self.econtext.EvaluationStack.Count, 0)

    def test_iter_array_values_bad(self):
        my_item = StackItem.New(12)
        self.econtext.EvaluationStack.PushT(my_item)
        self.engine.InvocationStack.PushT(self.econtext)

        result = self.state_reader.Iterator_Values(self.engine)

        self.assertEqual(result, False)
        self.assertEqual(self.econtext.EvaluationStack.Count, 0)

    def test_iter_array_keys_bad(self):

        my_item = StackItem.New(12)
        self.econtext.EvaluationStack.PushT(my_item)
        self.engine.InvocationStack.PushT(self.econtext)
        result = self.state_reader.Iterator_Keys(self.engine)

        self.assertEqual(result, False)
        self.assertEqual(self.econtext.EvaluationStack.Count, 0)
