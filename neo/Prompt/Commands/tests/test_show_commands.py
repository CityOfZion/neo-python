import os
from neo.Settings import settings
from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.Prompt.Commands.Show import CommandShow
from neo.Prompt.Commands.Wallet import CommandWallet
from neo.Prompt.PromptData import PromptData
from neo.bin.prompt import PromptInterface
from neo.Network.NodeLeader import NodeLeader, NeoNode
from neo.Core.Blockchain import Blockchain
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from mock import patch
from neo.Network.address import Address


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
        # test no block input
        args = ['block']
        res = CommandShow().execute(args)
        self.assertFalse(res)

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
        # test no header input
        args = ['header']
        res = CommandShow().execute(args)
        self.assertFalse(res)

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
        # test no tx input
        args = ['tx']
        res = CommandShow().execute(args)
        self.assertFalse(res)

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
        NodeLeader.Instance().Reset()
        leader = NodeLeader.Instance()
        addr1 = Address("127.0.0.1:20333")
        addr2 = Address("127.0.0.1:20334")
        leader.ADDRS = [addr1, addr2]
        leader.DEAD_ADDRS = [Address("127.0.0.1:20335")]
        test_node = NeoNode()
        test_node.host = "127.0.0.1"
        test_node.port = 20333
        test_node.address = Address("127.0.0.1:20333")
        leader.Peers = [test_node]

        # now show nodes
        with patch('neo.Network.NeoNode.NeoNode.Name', return_value="test name"):
            args = ['nodes']
            res = CommandShow().execute(args)
            self.assertTrue(res)
            self.assertIn('Total Connected: 1', res)
            self.assertIn('Peer 0', res)

            # now use "node"
            args = ['node']
            res = CommandShow().execute(args)
            self.assertTrue(res)
            self.assertIn('Total Connected: 1', res)
            self.assertIn('Peer 0', res)

    def test_show_state(self):
        # setup
        PromptInterface()

        args = ['state']
        res = CommandShow().execute(args)
        self.assertTrue(res)

    def test_show_notifications(self):
        # setup
        wallet_1_addr = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'

        # test with no NotificationDB
        with patch('neo.Implementations.Notifications.LevelDB.NotificationDB.NotificationDB.instance', return_value=None):
            args = ['notifications', wallet_1_addr]
            res = CommandShow().execute(args)
            self.assertFalse(res)

        # test with no input
        args = ['notifications']
        res = CommandShow().execute(args)
        self.assertFalse(res)

        # good test with address
        args = ['notifications', wallet_1_addr]
        res = CommandShow().execute(args)
        self.assertTrue(res)
        self.assertEqual(len(res), 1)
        jsn = res[0].ToJson()
        self.assertEqual(jsn['notify_type'], 'transfer')
        self.assertEqual(jsn['addr_from'], wallet_1_addr)

        # test an address with no notifications
        args = ['notifications', 'AZiE7xfyJALW7KmADWtCJXGGcnduYhGiCX']
        res = CommandShow().execute(args)
        self.assertFalse(res)

        # good test with contract
        contract_hash = "31730cc9a1844891a3bafd1aa929a4142860d8d3"
        args = ['notifications', contract_hash]
        res = CommandShow().execute(args)
        self.assertTrue(res)
        self.assertEqual(len(res), 1)
        jsn = res[0].ToJson()
        self.assertEqual(jsn['notify_type'], 'transfer')
        self.assertIn(contract_hash, jsn['contract'])

        # good test with contract 0x hash
        contract_hash = "0x31730cc9a1844891a3bafd1aa929a4142860d8d3"
        args = ['notifications', contract_hash]
        res = CommandShow().execute(args)
        self.assertTrue(res)
        self.assertEqual(len(res), 1)
        jsn = res[0].ToJson()
        self.assertEqual(jsn['notify_type'], 'transfer')
        self.assertEqual(contract_hash, jsn['contract'])

        # test contract not on the blockchain
        contract_hash = "3a4acd3647086e7c44398aac0349802e6a171129"  # NEX token hash
        args = ['notifications', contract_hash]
        res = CommandShow().execute(args)
        self.assertFalse(res)

        # good test with block index
        args = ['notifications', "12337"]
        res = CommandShow().execute(args)
        self.assertTrue(res)
        self.assertEqual(len(res), 1)
        jsn = res[0].ToJson()
        self.assertEqual(jsn['notify_type'], 'transfer')
        self.assertEqual(jsn['block'], 12337)

        # test block with no notifications
        args = ['notifications', "1"]
        res = CommandShow().execute(args)
        self.assertFalse(res)

        # test bad block
        index = Blockchain.Default().Height + 1
        args = ['notifications', str(index)]
        res = CommandShow().execute(args)
        self.assertFalse(res)

        # test invalid input
        args = ['notifications', "blah"]
        res = CommandShow().execute(args)
        self.assertFalse(res)

    def test_show_account(self):
        # setup
        wallet_1_addr = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'

        # test no account address entered
        args = ['account']
        res = CommandShow().execute(args)
        self.assertFalse(res)

        # test good account
        args = ['account', wallet_1_addr]
        res = CommandShow().execute(args)
        self.assertTrue(res)
        self.assertEqual(res['address'], wallet_1_addr)
        self.assertIn('balances', res)

        # test empty account
        with patch('neo.Prompt.PromptData.PromptData.Prompt'):
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=["testpassword", "testpassword"]):
                args = ['create', 'testwallet.wallet']
                res = CommandWallet().execute(args)
                self.assertTrue(res)
                self.assertIsInstance(res, UserWallet)

        addr = res.Addresses[0]
        args = ['account', addr]
        res = CommandShow().execute(args)
        self.assertFalse(res)

        # remove test wallet
        os.remove("testwallet.wallet")

    def test_show_asset(self):
        # test no asset entered
        args = ['asset']
        res = CommandShow().execute(args)
        self.assertFalse(res)

        # show all assets
        args = ['asset', 'all']
        res = CommandShow().execute(args)
        self.assertTrue(res)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[1]['NEO'], "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b")
        self.assertEqual(res[0]['NEOGas'], "0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7")

        # query with "neo"
        args = ['asset', 'neo']
        res = CommandShow().execute(args)
        self.assertTrue(res)
        self.assertEqual(res['assetId'], "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b")
        self.assertEqual(res['name'], "NEO")

        # query with "gas"
        args = ['asset', 'gas']
        res = CommandShow().execute(args)
        self.assertTrue(res)
        self.assertEqual(res['assetId'], "0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7")
        self.assertEqual(res['name'], "NEOGas")

        # query with scripthash
        args = ['asset', 'c56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b']
        res = CommandShow().execute(args)
        self.assertTrue(res)
        self.assertEqual(res['assetId'], "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b")
        self.assertEqual(res['name'], "NEO")

        # query with bad asset
        args = ['asset', 'c56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9e']
        res = CommandShow().execute(args)
        self.assertFalse(res)

        # query with bad input
        args = ['asset', 'blah']
        res = CommandShow().execute(args)
        self.assertFalse(res)

    def test_show_contract(self):
        # test no contract entered
        args = ['contract']
        res = CommandShow().execute(args)
        self.assertFalse(res)

        # show all contracts
        args = ['contract', 'all']
        res = CommandShow().execute(args)
        self.assertTrue(res)
        self.assertEqual(len(res), 6)
        self.assertEqual(res[0]["test NEX Template V4"], '0x31730cc9a1844891a3bafd1aa929a4142860d8d3')

        # query with contract scripthash
        args = ['contract', '31730cc9a1844891a3bafd1aa929a4142860d8d3']
        res = CommandShow().execute(args)
        self.assertTrue(res)
        self.assertEqual(res['name'], "test NEX Template V4")
        self.assertEqual(res['token']['name'], "NEX Template V4")
        self.assertEqual(res['token']['symbol'], "NXT4")

        # query with a contract scripthash not on the blockchain
        args = ['contract', '3a4acd3647086e7c44398aac0349802e6a171129']  # NEX token hash
        res = CommandShow().execute(args)
        self.assertFalse(res)

        # query bad input
        args = ['contract', 'blah']
        res = CommandShow().execute(args)
        self.assertFalse(res)
