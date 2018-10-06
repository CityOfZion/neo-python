import os

from boa_test.tests.boa_test import BoaTest
from boa.compiler import Compiler
from neo.Prompt.Commands.BuildNRun import TestBuild
from neo.EventHub import events, SmartContractEvent
from neo.Settings import settings


class TestNotifyDebugEvents(BoaTest):
    dispatched_events = []
    execution_success = False
    script = None

    @classmethod
    def setUpClass(cls):
        super(TestNotifyDebugEvents, cls).setUpClass()
        output = Compiler.instance().load('%s/ExecutionFailEventTest.py' % os.path.dirname(__file__)).default
        cls.script = output.write()
        settings.set_log_smart_contract_events(False)

    def on_fail_event(self, evt):
        self.dispatched_events.append(evt)

    def setUp(self):
        self.dispatched_events = []
        events.on(SmartContractEvent.EXECUTION_FAIL, self.on_fail_event)

    def tearDown(self):
        events.off(SmartContractEvent.EXECUTION_FAIL)

    def test_a_failed_execution(self):

        tx, results, total_ops, engine = TestBuild(self.script, ['testFail'], self.GetWallet1(), '01', '07')

        evt = self.dispatched_events.pop()
        fail_msg = 'Execution exited in a faulted state. Any payload besides this message contained in this event is the contents of the EvaluationStack of the current script context.'
        self.assertEqual(evt.event_payload.Value[0].Value, fail_msg)

        tx, results, total_ops, engine = TestBuild(self.script, ['testException'], self.GetWallet1(), '01', '07')

        evt = self.dispatched_events.pop()
        exception_message = b'An exception has been raised'
        self.assertEqual(evt.event_payload.Value[1].Value, exception_message)
