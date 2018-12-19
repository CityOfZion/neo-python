import os
from neo.Settings import settings
from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.Prompt.Commands.Config import CommandConfig
from copy import deepcopy
from neo.Network.NodeLeader import NodeLeader
from mock import patch
from io import StringIO


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
        args = ['output']
        with patch('neo.Prompt.Commands.Config.prompt', side_effect=[1, 1, 1, "\n", "\n"]):  # tests changing the level and keeping the current level
            res = CommandConfig().execute(args)
            self.assertTrue(res)
            self.assertEqual(res['generic'], "DEBUG")
            self.assertEqual(res['vm'], "DEBUG")
            self.assertEqual(res['db'], "DEBUG")
            self.assertEqual(res['peewee'], "ERROR")
            self.assertEqual(res['network'], "INFO")

    def test_config_sc_events(self):
        # test no input
        args = ['sc-events']
        res = CommandConfig().execute(args)
        self.assertFalse(res)

        # test turning them on
        args = ['sc-events', 'on']
        res = CommandConfig().execute(args)
        self.assertTrue(res)

        # test turning them off
        args = ['sc-events', '0']
        res = CommandConfig().execute(args)
        self.assertTrue(res)

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

        # test turning them off
        args = ['sc-debug-notify', '0']
        res = CommandConfig().execute(args)
        self.assertTrue(res)

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

        # test turning them off
        args = ['vm-log', '0']
        res = CommandConfig().execute(args)
        self.assertTrue(res)

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
        leader = NodeLeader.Instance()
        old_leader = deepcopy(leader)
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

        # restore whatever state the instance was in
        NodeLeader._LEAD = old_leader

    def test_config_maxpeers(self):
        # test no input
        args = ['maxpeers']
        res = CommandConfig().execute(args)
        self.assertFalse(res)

        # test changing the number of maxpeers
        args = ['maxpeers', "6"]
        res = CommandConfig().execute(args)
        self.assertTrue(res)
        self.assertEqual(int(res), settings.CONNECTED_PEER_MAX)

        # test bad input and verify the new number of maxpeers is maintained
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['maxpeers', "blah"]
            res = CommandConfig().execute(args)
            self.assertFalse(res)
            self.assertIn("Maintaining maxpeers at 6", mock_print.getvalue())

        # test negative number
        args = ['maxpeers', "-1"]
        res = CommandConfig().execute(args)
        self.assertFalse(res)
