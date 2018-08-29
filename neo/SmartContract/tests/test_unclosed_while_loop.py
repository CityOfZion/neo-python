import os
from boa_test.tests.boa_test import BoaTest
from boa.compiler import Compiler
from neo.Prompt.Commands.BuildNRun import TestBuild
from neo.VM.ExecutionEngine import ExecutionEngine
from mock import patch
from neo.Settings import settings
from logging import DEBUG, INFO
import binascii


class StringIn(str):
    def __eq__(self, other):
        return self in other


class TestUnclosedWhileLoop(BoaTest):
    engine = ExecutionEngine()
    script = None

    @classmethod
    def setUpClass(cls):
        super(TestUnclosedWhileLoop, cls).setUpClass()

        # the following script is a simple contract that is basically `while True`

        cls.script = binascii.unhexlify(b'00c56b620000')
        settings.set_loglevel(DEBUG)

    @classmethod
    def tearDownClass(cls):
        super(TestUnclosedWhileLoop, cls).tearDownClass()
        settings.set_loglevel(INFO)

    @patch('logzero.logger.debug')
    def test_unclosed_loop_script(self, mocked_logger):
        tx, results, total_ops, engine = TestBuild(self.script, [], self.GetWallet1(), '', 'ff')
        mocked_logger.assert_called_with(StringIn('Too many free operations processed'))
