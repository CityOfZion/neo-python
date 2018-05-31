import os
from boa_test.tests.boa_test import BoaTest
from boa.compiler import Compiler
from neo.Prompt.Commands.BuildNRun import TestBuild
from neo.VM.ExecutionEngine import ExecutionEngine
from mock import patch
from neo.Settings import settings
from logging import DEBUG, INFO


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
        settings.set_loglevel(DEBUG)

    @patch('logzero.logger.error')
    def test_invalid_array_index(self, mocked_logger):
        tx, results, total_ops, engine = TestBuild(self.script, [1, ['my_arg0']], self.GetWallet1(), '0210', '07')
        mocked_logger.assert_called_with(StringIn('Array index') and StringIn('exceeds list length'))

    @patch('logzero.logger.error')
    def test_negative_array_indexing(self, mocked_logger):
        tx, results, total_ops, engine = TestBuild(self.script, [2, ['my_arg0']], self.GetWallet1(), '0210', '07')
        mocked_logger.assert_called_with(StringIn("Array index is less than zero"))

    @patch('logzero.logger.error')
    def test_invalid_type_indexing(self, mocked_logger):
        tx, results, total_ops, engine = TestBuild(self.script, [3, ['my_arg0']], self.GetWallet1(), '0210', '07')
        mocked_logger.assert_called_with(StringIn("Cannot access item at index") and StringIn("Item is not an array or dict but of type"))

    @patch('logzero.logger.error')
    def test_invalid_appcall(self, mocked_logger):
        tx, results, total_ops, engine = TestBuild(self.script, [4, ['my_arg0']], self.GetWallet1(), '0210', '07', dynamic=True)
        mocked_logger.assert_called_with(StringIn("Trying to call an unknown contract"))

    # make sure this test is always last because we change the logging level
    @patch('logzero.logger.error')
    def test_no_logging_if_loglevel_not_debug(self, mocked_logger):
        settings.set_loglevel(INFO)
        tx, results, total_ops, engine = TestBuild(self.script, [1, ['my_arg0']], self.GetWallet1(), '0210', '07')
        self.assertEqual(0, mocked_logger.call_count)
