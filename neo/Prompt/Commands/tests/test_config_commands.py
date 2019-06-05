import os
from neo.Settings import settings
from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.Prompt.Commands.Config import CommandConfig
from neo.Network.nodemanager import NodeManager
from neo.Network.node import NeoNode
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
        with patch('neo.Prompt.Commands.Config.prompt',
                   side_effect=[1, 1, 1, "a", "\n", "\n"]):  # tests changing the level and keeping the current level. Entering "a" has no effect.
            res = CommandConfig().execute(args)
            self.assertTrue(res)
            self.assertEqual(res['generic'], "DEBUG")
            self.assertEqual(res['vm'], "DEBUG")
            self.assertEqual(res['db'], "DEBUG")
            self.assertEqual(res['peewee'], "ERROR")
            self.assertEqual(res['network'], "INFO")

        # test with keyboard interrupt
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Config.prompt', side_effect=[KeyboardInterrupt]):
                res = CommandConfig().execute(args)
                self.assertFalse(res)
                self.assertIn("Output configuration cancelled", mock_print.getvalue())

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

    def test_config_maxpeers(self):
        nodemgr = NodeManager()
        nodemgr.reset_for_test()

        # test no input and verify output confirming current maxpeers
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['maxpeers']
            res = CommandConfig().execute(args)
            self.assertFalse(res)
            self.assertEqual(settings.CONNECTED_PEER_MAX, 10)
            self.assertIn(f"Maintaining maxpeers at {settings.CONNECTED_PEER_MAX}", mock_print.getvalue())

        # test changing the number of maxpeers
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['maxpeers', "6"]
            res = CommandConfig().execute(args)
            self.assertTrue(res)
            self.assertEqual(settings.CONNECTED_PEER_MAX, 6)
            self.assertEqual(int(res), settings.CONNECTED_PEER_MAX)
            self.assertIn(f"Maxpeers set to {settings.CONNECTED_PEER_MAX}", mock_print.getvalue())

        # test trying to set maxpeers > 10
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['maxpeers', "12"]
            res = CommandConfig().execute(args)
            self.assertFalse(res)
            self.assertIn("Max peers is limited to 10", mock_print.getvalue())

        # test bad input
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['maxpeers', "blah"]
            res = CommandConfig().execute(args)
            self.assertFalse(res)
            self.assertIn("Invalid argument", mock_print.getvalue())

        # test negative number
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['maxpeers', "-1"]
            res = CommandConfig().execute(args)
            self.assertFalse(res)
            self.assertIn("Please supply a positive integer for maxpeers", mock_print.getvalue())

        # test if the new maxpeers < settings.CONNECTED_PEER_MAX
        # first make sure we have a predictable state
        node1 = NeoNode(object, object)
        node2 = NeoNode(object, object)
        node1.address = "127.0.0.1:20333"
        node2.address = "127.0.0.1:20334"

        nodemgr.nodes = [node1, node2]
        nodemgr.loop = object

        with patch("neo.Network.node.NeoNode.disconnect") as mock_disconnect:
            # first test if the number of connected peers !< new maxpeers
            self.assertEqual(nodemgr.max_clients, 6)  # verifying the current number of maxpeers
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['maxpeers', "4"]
                res = CommandConfig().execute(args)
                self.assertTrue(res)
                self.assertEqual(nodemgr.max_clients, 4)
                self.assertFalse(mock_disconnect.called)
                self.assertEqual(settings.CONNECTED_PEER_MAX, 4)
                self.assertIn(f"Maxpeers set to {settings.CONNECTED_PEER_MAX}", mock_print.getvalue())

            # now test if the number of connected peers < new maxpeers and < current minpeers
            self.assertEqual(settings.CONNECTED_PEER_MIN, 4)  # verifying the current minpeers value
            with patch('sys.stdout', new=StringIO()) as mock_print:
                with patch('neo.Prompt.Commands.Config.wait_for'):
                    args = ['maxpeers', "1"]
                    res = CommandConfig().execute(args)
                    self.assertTrue(res)
                    self.assertEqual(nodemgr.max_clients, 1)
                    self.assertTrue(mock_disconnect.called)
                    self.assertEqual(settings.CONNECTED_PEER_MAX, 1)
                    self.assertIn(f"Maxpeers set to {settings.CONNECTED_PEER_MAX}", mock_print.getvalue())

                    self.assertEqual(settings.CONNECTED_PEER_MIN, 1)
                    self.assertIn(f"Minpeers set to {settings.CONNECTED_PEER_MIN}", mock_print.getvalue())

        # reset for future tests
        nodemgr.reset_for_test()
        nodemgr.loop = None
        settings.set_max_peers(10)

    def test_config_minpeers(self):
        # test no input and verify output confirming current minpeers
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['minpeers']
            res = CommandConfig().execute(args)
            self.assertFalse(res)
            self.assertIn(f"Maintaining minpeers at {settings.CONNECTED_PEER_MIN}", mock_print.getvalue())

        # test changing the number of minpeers
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['minpeers', "6"]
            res = CommandConfig().execute(args)
            self.assertTrue(res)
            self.assertEqual(int(res), settings.CONNECTED_PEER_MIN)
            self.assertIn(f"Minpeers set to {settings.CONNECTED_PEER_MIN}", mock_print.getvalue())

        # test bad input
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['minpeers', "blah"]
            res = CommandConfig().execute(args)
            self.assertFalse(res)
            self.assertIn("Please supply a positive integer for minpeers", mock_print.getvalue())

        # test negative number
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['minpeers', "-1"]
            res = CommandConfig().execute(args)
            self.assertFalse(res)
            self.assertIn("Please supply a positive integer for minpeers", mock_print.getvalue())

        # test minpeers greater than maxpeers
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['minpeers', f"{settings.CONNECTED_PEER_MAX + 1}"]
            res = CommandConfig().execute(args)
            self.assertFalse(res)
            self.assertIn("minpeers setting cannot be bigger than maxpeers setting", mock_print.getvalue())

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
