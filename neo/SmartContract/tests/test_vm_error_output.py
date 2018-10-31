import os
from boa_test.tests.boa_test import BoaTest
from boa.compiler import Compiler
from neo.Prompt.Commands.BuildNRun import TestBuild
from neo.VM.ExecutionEngine import ExecutionEngine
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

    def test_invalid_array_index(self):
        with self.assertLogHandler('vm', DEBUG) as log_context:
            tx, results, total_ops, engine = TestBuild(self.script, [1, ['my_arg0']], self.GetWallet1(), '0210', '07')
            self.assertTrue(len(log_context.output) > 0)
            log_msg = log_context.output[0]
            self.assertTrue("Array index" in log_msg and "exceeds list length" in log_msg)

    def test_negative_array_indexing(self):
        with self.assertLogHandler('vm', DEBUG) as log_context:
            tx, results, total_ops, engine = TestBuild(self.script, [2, ['my_arg0']], self.GetWallet1(), '0210', '07')
            self.assertTrue(len(log_context.output) > 0)
            log_msg = log_context.output[0]
            self.assertTrue("Array index is less than zero" in log_msg)

    def test_invalid_type_indexing(self):
        with self.assertLogHandler('vm', DEBUG) as log_context:
            tx, results, total_ops, engine = TestBuild(self.script, [3, ['my_arg0']], self.GetWallet1(), '0210', '07')
            self.assertTrue(len(log_context.output) > 0)
            log_msg = log_context.output[0]
            self.assertTrue("Cannot access item at index" in log_msg and "Item is not an array or dict but of type" in log_msg)

    def test_invalid_appcall(self):
        with self.assertLogHandler('vm', DEBUG) as log_context:
            tx, results, total_ops, engine = TestBuild(self.script, [4, ['my_arg0']], self.GetWallet1(), '0210', '07', dynamic=True)
            self.assertTrue(len(log_context.output) > 1)
            log_msg = log_context.output[1]
            self.assertTrue("Trying to call an unknown contract" in log_msg)

    def test_no_logging_if_loglevel_not_debug(self):
        with self.assertLogHandler('vm', INFO) as log_context:
            tx, results, total_ops, engine = TestBuild(self.script, [1, ['my_arg0']], self.GetWallet1(), '0210', '07')
            self.assertEqual(len(log_context.output), 0)
