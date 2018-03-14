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
        output = Compiler.instance().load('%s/sc_debug_events.py' % os.path.dirname(__file__)).default
        cls.script = output.write()

        settings.set_log_smart_contract_events(False)

    def on_info_event(self, evt):
        self.dispatched_events.append(evt)

    def on_execution(self, evt):
        self.execution_success = evt.execution_success

    def setUp(self):
        self.dispatched_events = []
        self.execution_success = False

        events.on(SmartContractEvent.RUNTIME_NOTIFY, self.on_info_event)
        events.on(SmartContractEvent.RUNTIME_LOG, self.on_info_event)
        events.on(SmartContractEvent.EXECUTION, self.on_execution)

    def tearDown(self):
        events.off(SmartContractEvent.RUNTIME_NOTIFY, self.on_info_event)
        events.off(SmartContractEvent.RUNTIME_LOG, self.on_info_event)
        events.off(SmartContractEvent.EXECUTION, self.on_execution)

    def test_validate_normal_behaviour(self):
        """
        Test that 'sc-debug-notify' is off by default and the output produces out of order messaging on successful SC execution.
        """
        settings.set_emit_notify_events_on_sc_execution_error(False)

        tx, results, total_ops, engine = TestBuild(self.script, [['my_arg0']], self.GetWallet1(), '10', '07')

        self.assertTrue(self.execution_success)
        self.assertEqual('my_arg0', self.dispatched_events[0].event_payload[0].decode())
        self.assertEqual(SmartContractEvent.RUNTIME_LOG, self.dispatched_events[0].event_type)
        self.assertEqual('Start main', self.dispatched_events[1].event_payload[0].decode())
        self.assertEqual(SmartContractEvent.RUNTIME_NOTIFY, self.dispatched_events[1].event_type)

    def test_validate_normal_behaviour2(self):
        """
        Test that 'sc-debug-notify' is off by default and that no notifications are logged when SC execution fails.
        """
        settings.set_emit_notify_events_on_sc_execution_error(False)

        tx, results, total_ops, engine = TestBuild(self.script, ['invalid_arg'], self.GetWallet1(), '10', '07')

        self.assertFalse(self.execution_success)
        self.assertEqual(0, len(self.dispatched_events))

    def test_debug_notify_events(self):
        """
        Test that we still output all Notify events prior to the point of failure when SC execution fails.
        """
        settings.set_emit_notify_events_on_sc_execution_error(True)

        tx, results, total_ops, engine = TestBuild(self.script, ['invalid_arg'], self.GetWallet1(), '10', '07')

        self.assertFalse(self.execution_success)
        self.assertEqual(SmartContractEvent.RUNTIME_NOTIFY, self.dispatched_events[0].event_type)
        self.assertEqual('Start main', self.dispatched_events[0].event_payload[0].decode())
        self.assertEqual(1, len(self.dispatched_events))
