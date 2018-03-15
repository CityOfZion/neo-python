import os
from boa_test.tests.boa_test import BoaTest
from boa.compiler import Compiler
from neo.Prompt.Commands.BuildNRun import TestBuild
from neo.VM.ExecutionEngine import ExecutionEngine
from mock import patch


class StringIn(str):
    def __eq__(self, other):
        return self in other


class TestVMErrors(BoaTest):
    engine = ExecutionEngine()
    script = None

    @classmethod
    def setUpClass(cls):
        super(TestVMErrors, cls).setUpClass()
        output = Compiler.instance().load('%s/sc_vm_errors.py' % os.path.dirname(__file__)).default
        cls.script = output.write()

    @patch('logzero.logger.error')
    def test_invalid_array_index(self, mocked_logger):
        tx, results, total_ops, engine = TestBuild(self.script, [1, ['my_arg0']], self.GetWallet1(), '0210', '07')
        mocked_logger.assert_called_with(StringIn('Array index') and StringIn('exceeds list length'))

    @patch('logzero.logger.error')
    def test_negative_array_indexing(self, mocked_logger):
        tx, results, total_ops, engine = TestBuild(self.script, [2, ['my_arg0']], self.GetWallet1(), '0210', '07')
        mocked_logger.assert_called_with(StringIn("Attempting to access an array using a negative index"))

    @patch('logzero.logger.error')
    def test_invalid_type_indexing(self, mocked_logger):
        tx, results, total_ops, engine = TestBuild(self.script, [3, ['my_arg0']], self.GetWallet1(), '0210', '07')
        mocked_logger.assert_called_with(StringIn("Cannot access item at index") and StringIn("Item is not an array but of type"))

    @patch('logzero.logger.error')
    def test_invalid_appcall(self, mocked_logger):
        tx, results, total_ops, engine = TestBuild(self.script, [4, ['my_arg0']], self.GetWallet1(), '0210', '07', dynamic=True)
        mocked_logger.assert_called_with(StringIn("Trying to call an unknown contract"))
