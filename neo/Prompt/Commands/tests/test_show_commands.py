import os
from neo.Settings import settings
from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.Prompt.Commands.Show import CommandShow
from neo.Prompt.Commands.Wallet import CommandWallet
from neo.Prompt.PromptData import PromptData
from neo.bin.prompt import PromptInterface
from copy import deepcopy
from neo.Network.NodeLeader import NodeLeader, NeoNode
from neo.Core.Blockchain import Blockchain
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from mock import patch


class CommandShowTestCase(BlockchainFixtureTestCase):

    @classmethod
    def leveldb_testpath(self):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    @classmethod
    def tearDown(cls):
        PromptData.Prompt = None
        PromptData.Wallet = None

    def test_show(self):
        # with no subcommand
        res = CommandShow().execute(None)
        self.assertFalse(res)

        # with invalid command
        args = ['badcommand']
        res = CommandShow().execute(args)
        self.assertFalse(res)

    def test_show_block(self):
        # show good block by index
        args = ['block', '9']
        res = CommandShow().execute(args)
        self.assertTrue(res)
        self.assertEqual(res['index'], 9)
        self.assertIn('tx', res)

        # show good block by hash
        args = ['block', "0x7c5b4c8a70336bf68e8679be7c9a2a15f85c0f6d0e14389019dcc3edfab2bb4b"]
        res = CommandShow().execute(args)
        self.assertTrue(res)
        self.assertEqual(res['index'], 9)
        self.assertIn('tx', res)

        # show the block's transactions only
        args = ['block', '9', "tx"]
        res = CommandShow().execute(args)
        self.assertTrue(res)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]['type'], "MinerTransaction")
        self.assertEqual(res[1]['type'], "ContractTransaction")

        # request bad block
        args = ['block', 'blah']
        res = CommandShow().execute(args)
        self.assertFalse(res)

    def test_show_header(self):
        # show good header by index
        args = ['header', '9']
        res = CommandShow().execute(args)
        self.assertTrue(res)
        self.assertEqual(res['index'], 9)
        self.assertNotIn('tx', res)

        # show good header by hash
        args = ['header', "0x7c5b4c8a70336bf68e8679be7c9a2a15f85c0f6d0e14389019dcc3edfab2bb4b"]
        res = CommandShow().execute(args)
        self.assertTrue(res)
        self.assertEqual(res['index'], 9)
        self.assertNotIn('tx', res)

        # request bad header
        args = ['header', 'blah']
        res = CommandShow().execute(args)
        self.assertFalse(res)

    def test_show_tx(self):
        # show good tx
        txid = '0x83df8bd085fcb60b2789f7d0a9f876e5f3908567f7877fcba835e899b9dea0b5'
        args = ['tx', txid]
        res = CommandShow().execute(args)
        self.assertTrue(res)
        self.assertEqual(res['txid'], txid)
        self.assertIn('height', res)
        self.assertIn('unspents', res)

        # query a bad tx
        args = ['tx', '0x83df8bd085fcb60b2789f7d0a9f876e5f3908567f7877fcba835e899b9dea0b6']
        res = CommandShow().execute(args)
        self.assertFalse(res)

        # query with bad args
        args = ['tx', 'blah']
        res = CommandShow().execute(args)
        self.assertFalse(res)

    def test_show_mem(self):
        args = ['mem']
        res = CommandShow().execute(args)
        self.assertTrue(res)

    def test_show_nodes(self):
        # query nodes with no NodeLeader.Instance()
        with patch('neo.Network.NodeLeader.NodeLeader.Instance'):
            args = ['nodes']
            res = CommandShow().execute(args)
            self.assertFalse(res)

        # query nodes with connected peers
        # first make sure we have a predictable state
        leader = NodeLeader.Instance()
        old_leader = deepcopy(leader)
        leader.ADDRS = ["127.0.0.1:20333", "127.0.0.2:20334"]
        leader.DEAD_ADDRS = ["127.0.0.1:20335"]
        test_node = NeoNode()
        test_node.host = "127.0.0.1"
        test_node.port = 20333
        leader.Peers = [test_node]

        # now show nodes
        with patch('neo.Network.NeoNode.NeoNode.Name', return_value="test name"):
            args = ['nodes']
            res = CommandShow().execute(args)
            self.assertTrue(res)
            self.assertIn('Total Connected: 1', res)
            self.assertIn('Peer test name - IO: 0.0 MB in / 0.0 MB out', res)

            # now use "node"
            args = ['node']
            res = CommandShow().execute(args)
            self.assertTrue(res)
            self.assertIn('Total Connected: 1', res)
            self.assertIn('Peer test name - IO: 0.0 MB in / 0.0 MB out', res)

        # restore whatever state the instance was in
        NodeLeader._LEAD = old_leader
