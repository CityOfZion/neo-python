from unittest import TestCase
from neo.VM.InteropService import Struct, StackItem, Array, Boolean, Map
from neo.VM.ExecutionEngine import ExecutionEngine
from neo.VM.ExecutionEngine import ExecutionContext
from neo.SmartContract.StateReader import StateReader
from neocore.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import StreamManager
from neo.Core.Blockchain import Blockchain
from mock import patch

from neo.SmartContract.tests.test_vm_error_output import StringIn


class InteropSerializeDeserializeTestCase(TestCase):

    engine = None
    econtext = None
    state_reader = None

    def setUp(self):
        self.engine = ExecutionEngine()
        self.econtext = ExecutionContext()
        self.state_reader = StateReader()

    def test_serialize_struct(self):

        my_struct = Struct([StackItem.New(12),
                            StackItem.New(b'Hello World'),
                            StackItem.New(True),
                            Array([StackItem.New(113442), StackItem.New(2), StackItem.New(3)])
                            ])
        self.engine.EvaluationStack.PushT(my_struct)
        self.state_reader.Runtime_Serialize(self.engine)
        self.state_reader.Runtime_Deserialize(self.engine)

        deserialized = self.engine.EvaluationStack.Pop()
        self.assertIsInstance(deserialized, Struct)
        self.assertEqual(deserialized.Count, 4)
        self.assertEqual(deserialized.GetArray()[0], StackItem.New(12))
        self.assertEqual(deserialized.GetArray()[1], StackItem.New(b'Hello World'))
        self.assertEqual(deserialized.GetArray()[2], StackItem.New(True))
        subarray = deserialized.GetArray()[3]
        self.assertIsInstance(subarray, Array)
        self.assertEqual(subarray.Count, 3)
        self.assertEqual(subarray.GetArray()[0], StackItem.New(113442))

    def test_serialize_array(self):

        my_array = Array([StackItem.New(12),
                          StackItem.New(b'Hello World'),
                          StackItem.New(True),
                          Array([StackItem.New(113442), StackItem.New(2), StackItem.New(3)])
                          ])
        self.engine.EvaluationStack.PushT(my_array)
        self.state_reader.Runtime_Serialize(self.engine)
        self.state_reader.Runtime_Deserialize(self.engine)

        deserialized = self.engine.EvaluationStack.Pop()
        self.assertIsInstance(deserialized, Array)
        self.assertEqual(deserialized.Count, 4)
        self.assertEqual(deserialized.GetArray()[0], StackItem.New(12))
        self.assertEqual(deserialized.GetArray()[1], StackItem.New(b'Hello World'))
        self.assertEqual(deserialized.GetArray()[2], StackItem.New(True))
        subarray = deserialized.GetArray()[3]
        self.assertIsInstance(subarray, Array)
        self.assertEqual(subarray.Count, 3)
        self.assertEqual(subarray.GetArray()[0], StackItem.New(113442))

    def test_serialize_bytearray(self):
        my_ba = StackItem.New(b'a0f03a')
        self.engine.EvaluationStack.PushT(my_ba)
        self.state_reader.Runtime_Serialize(self.engine)
        res = self.state_reader.Runtime_Deserialize(self.engine)

        deserialized = self.engine.EvaluationStack.Pop()
        self.assertEqual(deserialized.GetByteArray(), bytearray(b'a0f03a'))

        my_ba = StackItem.New(b'Hello Serialization')
        self.engine.EvaluationStack.PushT(my_ba)
        self.state_reader.Runtime_Serialize(self.engine)
        self.state_reader.Runtime_Deserialize(self.engine)

        deserialized = self.engine.EvaluationStack.Pop()
        self.assertEqual(deserialized.GetByteArray(), bytearray(b'Hello Serialization'))

        my_ba = StackItem.New(bytearray(b'\x01\x03\xfa\x99\x42'))
        self.engine.EvaluationStack.PushT(my_ba)
        self.state_reader.Runtime_Serialize(self.engine)
        self.state_reader.Runtime_Deserialize(self.engine)

        deserialized = self.engine.EvaluationStack.Pop()
        self.assertEqual(deserialized.GetByteArray(), bytearray(b'\x01\x03\xfa\x99\x42'))

    def test_serialize_bool(self):
        # create integer, serialize it via state reader
        my_bool = StackItem.New(True)
        self.engine.EvaluationStack.PushT(my_bool)
        self.state_reader.Runtime_Serialize(self.engine)
        self.state_reader.Runtime_Deserialize(self.engine)

        deserialized = self.engine.EvaluationStack.Pop()
        self.assertIsInstance(deserialized, Boolean)
        self.assertEqual(deserialized.GetBoolean(), True)

        my_bool = StackItem.New(False)
        self.engine.EvaluationStack.PushT(my_bool)
        self.state_reader.Runtime_Serialize(self.engine)
        self.state_reader.Runtime_Deserialize(self.engine)

        deserialized = self.engine.EvaluationStack.Pop()
        self.assertIsInstance(deserialized, Boolean)
        self.assertEqual(deserialized.GetBoolean(), False)

    def test_serialize_integer(self):

        # create integer, serialize it via state reader
        my_integer = StackItem.New(1234)
        self.engine.EvaluationStack.PushT(my_integer)
        self.state_reader.Runtime_Serialize(self.engine)
        self.assertEqual(len(self.engine.EvaluationStack.Items), 1)

        # we will preview what will be pushed onto the stack
        existing = self.engine.EvaluationStack.Peek(0)
        ms = StreamManager.GetStream(existing.GetByteArray())
        reader = BinaryReader(ms)
        result = StackItem.DeserializeStackItem(reader)

        # now run deserialized
        res = self.state_reader.Runtime_Deserialize(self.engine)
        self.assertEqual(res, True)

        deserialized = self.engine.EvaluationStack.Pop()

        self.assertEqual(deserialized, result)
        self.assertEqual(deserialized, my_integer)
        self.assertEqual(deserialized.GetBigInteger(), 1234)

    def test_serialize_negative_integer(self):

        # create integer, serialize it via state reader
        my_integer = StackItem.New(-12324345)
        self.engine.EvaluationStack.PushT(my_integer)
        self.state_reader.Runtime_Serialize(self.engine)
        self.state_reader.Runtime_Deserialize(self.engine)

        deserialized = self.engine.EvaluationStack.Pop()

#        self.assertEqual(deserialized, my_integer)
        self.assertEqual(deserialized.GetBigInteger(), -12324345)

    def test_serialize_big_integer(self):
        # create integer, serialize it via state reader
        my_integer = StackItem.New(23424324242424242424234)
        self.engine.EvaluationStack.PushT(my_integer)
        self.state_reader.Runtime_Serialize(self.engine)
        self.state_reader.Runtime_Deserialize(self.engine)

        deserialized = self.engine.EvaluationStack.Pop()

        #        self.assertEqual(deserialized, my_integer)
        self.assertEqual(deserialized.GetBigInteger(), 23424324242424242424234)

    def test_serialize_zero(self):
        # create integer, serialize it via state reader
        my_integer = StackItem.New(0)
        self.engine.EvaluationStack.PushT(my_integer)
        self.state_reader.Runtime_Serialize(self.engine)
        self.state_reader.Runtime_Deserialize(self.engine)

        deserialized = self.engine.EvaluationStack.Pop()
        self.assertEqual(deserialized.GetBigInteger(), 0)

    def test_serialize_map(self):
        map2 = Map({
            StackItem.New(b'a'): StackItem.New(1),
            StackItem.New(b'b'): StackItem.New(2),
            StackItem.New(b'c'): StackItem.New(3),
        })

        self.engine.EvaluationStack.PushT(map2)

        self.state_reader.Runtime_Serialize(self.engine)
        self.state_reader.Runtime_Deserialize(self.engine)

        deserialized = self.engine.EvaluationStack.Pop()
        self.assertEqual(deserialized, map2)

        map3 = Map({
            StackItem.New(b'j'): StackItem.New(8),
            StackItem.New(b'k'): StackItem.New(2222),
        })

        map2.SetItem(StackItem.New(b'mymap'), map3)

        self.engine.EvaluationStack.PushT(map2)

        self.state_reader.Runtime_Serialize(self.engine)
        self.state_reader.Runtime_Deserialize(self.engine)

        deserialized = self.engine.EvaluationStack.Pop()
        self.assertEqual(deserialized, map2)

    @patch('logzero.logger.error')
    def test_cant_serialize_iop_item(self, mocked_logger):

        genesis = Blockchain.GenesisBlock()
        self.engine.EvaluationStack.PushT(StackItem.FromInterface(genesis))
        cant_do = self.state_reader.Runtime_Serialize(self.engine)
        self.assertEqual(cant_do, False)
        mocked_logger.assert_called_with(StringIn('Cannot serialize item IOp Interface: <neo.Core.Block.Block object'))

    @patch('logzero.logger.error')
    def test_cant_deserialize_item(self, mocked_logger):

        self.engine.EvaluationStack.PushT(StackItem.New(b'abc'))
        self.state_reader.Runtime_Deserialize(self.engine)
        item = self.engine.EvaluationStack.Pop()
        self.assertIsNone(item)
        mocked_logger.assert_called_with(StringIn('Could not deserialize stack item with type:'))
