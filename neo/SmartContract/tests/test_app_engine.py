from neo.Utils.NeoTestCase import NeoTestCase
from neo.VM.InteropService import Array, Map, Integer, BigInteger
from neo.SmartContract.ApplicationEngine import ApplicationEngine
from neo.VM.ExecutionContext import ExecutionContext
from neo.SmartContract import TriggerType
from mock import Mock, MagicMock
from neo.VM.Script import Script


class TestApplicationEngine(NeoTestCase):

    def setUp(self):
        gas_mock = MagicMock()
        gas_mock.value.return_value = 0
        self.engine = ApplicationEngine(TriggerType.Application, Mock(), Mock(), gas_mock, MagicMock())

    def test_get_item_count(self):
        econtext1 = ExecutionContext(Script(self.engine.Crypto, b''), 0)
        # 4 items in context 1
        map = Map.FromDictionary({'a': 1, 'b': 2, 'c': 3})
        my_int = Integer(BigInteger(1))
        econtext1.EvaluationStack.PushT(map)
        econtext1.EvaluationStack.PushT(my_int)

        # 3 items in context 2
        econtext2 = ExecutionContext(Script(self.engine.Crypto, b''), 0)
        my_array = Array([my_int, my_int])
        econtext2.EvaluationStack.PushT(my_array)
        econtext2.AltStack.PushT(my_int)

        self.engine.InvocationStack.PushT(econtext1)
        self.engine.InvocationStack.PushT(econtext2)

        stack_item_list = []
        for execution_context in self.engine.InvocationStack.Items:  # type: ExecutionContext
            stack_item_list += execution_context.EvaluationStack.Items + execution_context.AltStack.Items

        self.assertEqual(7, self.engine.GetItemCount(stack_item_list))
