from boa_test.tests.boa_test import BoaTest
from neo.Prompt.Commands.BuildNRun import TestBuild
from neo.VM.ExecutionEngine import ExecutionEngine
from neo.Settings import settings
from logging import DEBUG, INFO
import binascii


class TestUnclosedWhileLoop(BoaTest):
    engine = ExecutionEngine()
    script = None

    @classmethod
    def setUpClass(cls):
        super(TestUnclosedWhileLoop, cls).setUpClass()

        # the following script is a simple contract that is basically `while True`

        cls.script = binascii.unhexlify(b'00c56b620000')

    @classmethod
    def tearDownClass(cls):
        super(TestUnclosedWhileLoop, cls).tearDownClass()

    def test_unclosed_loop_script(self):
        with self.assertLogHandler('vm', DEBUG) as log_context:
            tx, results, total_ops, engine = TestBuild(self.script, [], self.GetWallet1(), '', 'ff')
            self.assertTrue(len(log_context.output) > 0)
            self.assertTrue("Too many free operations processed" in log_context.output[0])
