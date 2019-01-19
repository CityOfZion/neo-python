import os
from neo.Settings import settings
from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.Prompt.Commands.Config import CommandConfig
from copy import deepcopy
from neo.Network.NodeLeader import NodeLeader
from mock import patch
from io import StringIO
from neo.Prompt.PromptPrinter import pp


class CommandConfigTestCase(BlockchainFixtureTestCase):
    @classmethod
    def leveldb_testpath(self):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    def test_config(self):
        # with no subcommand
        res = CommandConfig().execute(None)
        self.assertFalse(res)

        # with invalid command
        args = ['badcommand']
        res = CommandConfig().execute(args)
        self.assertFalse(res)

    def test_config_output(self):
        # importing because it sets up `peewee` logging, which is checked at the test below
        from neo.Implementations.Wallets.peewee.UserWallet import UserWallet

        args = ['output']
        with patch('neo.Prompt.Commands.Config.prompt', side_effect=[1, 1, 1, "\n", "\n", "\n"]):  # tests changing the level and keeping the current level
            res = CommandConfig().execute(args)
            self.assertTrue(res)
            self.assertEqual(res['generic'], "DEBUG")
            self.assertEqual(res['vm'], "DEBUG")
            self.assertEqual(res['db'], "DEBUG")
            self.assertEqual(res['peewee'], "ERROR")
            self.assertEqual(res['network'], "INFO")
            self.assertEqual(res['network.verbose'], "INFO")

    def test_config_sc_events(self):
        # test no input
        args = ['sc-events']
        res = CommandConfig().execute(args)
        self.assertFalse(res)

        # test turning them on
        args = ['sc-events', 'on']
        res = CommandConfig().execute(args)
        self.assertTrue(res)
        self.assertTrue(settings.log_smart_contract_events)

        # test turning them off
        args = ['sc-events', '0']
        res = CommandConfig().execute(args)
        self.assertTrue(res)
        self.assertFalse(settings.log_smart_contract_events)

        # test bad input
        args = ['sc-events', 'blah']
        res = CommandConfig().execute(args)
        self.assertFalse(res)

    def test_config_debug_notify(self):
        # test no input
        args = ['sc-debug-notify']
        res = CommandConfig().execute(args)
        self.assertFalse(res)

        # test turning them on
        args = ['sc-debug-notify', 'on']
        res = CommandConfig().execute(args)
        self.assertTrue(res)
        self.assertTrue(settings.emit_notify_events_on_sc_execution_error)

        # test turning them off
        args = ['sc-debug-notify', '0']
        res = CommandConfig().execute(args)
        self.assertTrue(res)
        self.assertFalse(settings.emit_notify_events_on_sc_execution_error)

        # test bad input
        args = ['sc-debug-notify', 'blah']
        res = CommandConfig().execute(args)
        self.assertFalse(res)

    def test_config_vm_log(self):
        # test no input
        args = ['vm-log']
        res = CommandConfig().execute(args)
        self.assertFalse(res)

        # test turning them on
        args = ['vm-log', 'on']
        res = CommandConfig().execute(args)
        self.assertTrue(res)
        self.assertTrue(settings.log_vm_instructions)

        # test turning them off
        args = ['vm-log', '0']
        res = CommandConfig().execute(args)
        self.assertTrue(res)
        self.assertFalse(settings.log_vm_instructions)

        # test bad input
        args = ['vm-log', 'blah']
        res = CommandConfig().execute(args)
        self.assertFalse(res)

    def test_config_node_requests(self):
        # test no input
        args = ['node-requests']
        res = CommandConfig().execute(args)
        self.assertFalse(res)

        # test updating block request size
        # first make sure we have a predictable state
        NodeLeader.Instance().Reset()
        leader = NodeLeader.Instance()
        leader.ADDRS = ["127.0.0.1:20333", "127.0.0.2:20334"]
        leader.DEAD_ADDRS = ["127.0.0.1:20335"]

        # test slow setting
        args = ['node-requests', 'slow']
        res = CommandConfig().execute(args)
        self.assertTrue(res)

        # test normal setting
        args = ['node-requests', 'normal']
        res = CommandConfig().execute(args)
        self.assertTrue(res)

        # test fast setting
        args = ['node-requests', 'fast']
        res = CommandConfig().execute(args)
        self.assertTrue(res)

        # test bad setting
        args = ['node-requests', 'blah']
        res = CommandConfig().execute(args)
        self.assertFalse(res)

        # test custom setting
        args = ['node-requests', '20', '6000']
        res = CommandConfig().execute(args)
        self.assertTrue(res)

        # test bad custom input
        args = ['node-requests', '20', 'blah']
        res = CommandConfig().execute(args)
        self.assertFalse(res)

        # test bad custom setting: breqmax should be greater than breqpart
        args = ['node-requests', '20', '10']
        res = CommandConfig().execute(args)
        self.assertFalse(res)

        # test another bad custom setting: breqpart should not exceed 500
        args = ['node-requests', '600', '5000']
        res = CommandConfig().execute(args)
        self.assertFalse(res)

    def test_config_maxpeers(self):
        # test no input and verify output confirming current maxpeers
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['maxpeers']
            res = CommandConfig().execute(args)
            self.assertFalse(res)
            self.assertIn(f"Maintaining maxpeers at {settings.CONNECTED_PEER_MAX}", mock_print.getvalue())

        # test changing the number of maxpeers
        args = ['maxpeers', "6"]
        res = CommandConfig().execute(args)
        self.assertTrue(res)
        self.assertEqual(int(res), settings.CONNECTED_PEER_MAX)

        # test bad input
        args = ['maxpeers', "blah"]
        res = CommandConfig().execute(args)
        self.assertFalse(res)

        # test negative number
        args = ['maxpeers', "-1"]
        res = CommandConfig().execute(args)
        self.assertFalse(res)

    def test_config_nep8(self):
        # test with missing flag argument
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['nep8']
            res = CommandConfig().execute(args)
            self.assertFalse(res)
            self.assertIn("Please specify the required parameter", mock_print.getvalue())

        # test with invalid option
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['nep8', 'blah']
            res = CommandConfig().execute(args)
            self.assertFalse(res)
            self.assertIn("Invalid option", mock_print.getvalue())

        # ideally for the next tests we should compile some SC and validate if NEP-8 instructions are used or not
        # for now the effort required to do so does not seem justified and we'll just rely on applying the setting

        # test turning on - 1
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['nep8', 'on']
            res = CommandConfig().execute(args)
            self.assertTrue(res)
            self.assertIn("NEP-8 compiler instruction usage is ON", mock_print.getvalue())

        # test turning on - 2
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['nep8', '1']
            res = CommandConfig().execute(args)
            self.assertTrue(res)
            self.assertIn("NEP-8 compiler instruction usage is ON", mock_print.getvalue())

        # test turning off - 1
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['nep8', 'off']
            res = CommandConfig().execute(args)
            self.assertTrue(res)
            self.assertIn("NEP-8 compiler instruction usage is OFF", mock_print.getvalue())

        # test turning off - 2
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['nep8', '0']
            res = CommandConfig().execute(args)
            self.assertTrue(res)
            self.assertIn("NEP-8 compiler instruction usage is OFF", mock_print.getvalue())
