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


class TestVMErrors(BoaTest):
    engine = ExecutionEngine()
    script = None

    @classmethod
    def setUpClass(cls):
        super(TestVMErrors, cls).setUpClass()
        output = Compiler.instance().load('%s/sc_vm_errors.py' % os.path.dirname(__file__)).default
        cls.script = binascii.unhexlify(b'00c56b620000')
        settings.set_loglevel(DEBUG)

    @patch('logzero.logger.error')
    def test_invalid_array_index(self, mocked_logger):
        tx, results, total_ops, engine = TestBuild(self.script, [], self.GetWallet1(), '', 'ff')
        mocked_logger.assert_called_with(StringIn('Too many free operations processed'))
