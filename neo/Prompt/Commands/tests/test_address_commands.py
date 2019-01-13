from neo.Prompt.Commands.Wallet import CommandWallet
from neo.Prompt.Commands.tests.test_wallet_commands import UserWalletTestCaseBase
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Prompt.PromptData import PromptData
from neo.Prompt.Commands.WalletAddress import SplitUnspentCoin, CreateAddress
from neo.Core.TX.Transaction import ContractTransaction
from neocore.Fixed8 import Fixed8
from mock import patch
from io import StringIO
import os


class UserWalletTestCase(UserWalletTestCaseBase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_wallet_create_address(self):
        # test wallet create address with no wallet open
        args = ['address', 'create', 1]
        res = CommandWallet().execute(args)
        self.assertFalse(res)

        self.OpenWallet1()

        # test wallet create address with no argument
        args = ['address', 'create']
        res = CommandWallet().execute(args)
        self.assertFalse(res)

        # test wallet create address with negative number
        args = ['address', 'create', -1]
        res = CommandWallet().execute(args)
        self.assertFalse(res)

        # test wallet create address successful
        args = ['address', 'create', 1]
        res = CommandWallet().execute(args)
        self.assertTrue(res)
        self.assertEqual(type(res), UserWallet)
        self.assertEqual(len(res.Addresses), 2)  # Has one address when created.

        args = ['address', 'create', 7]
        res = CommandWallet().execute(args)
        self.assertTrue(res)
        self.assertEqual(type(res), UserWallet)
        self.assertEqual(len(res.Addresses), 9)

    def test_wallet_delete_address(self):
        # test wallet delete address with no wallet open
        args = ['address', 'delete']
        res = CommandWallet().execute(args)
        self.assertFalse(res)

        self.OpenWallet1()

        # test wallet delete address with no argument
        args = ['address', 'delete']
        res = CommandWallet().execute(args)
        self.assertFalse(res)

        # test wallet delete address with invalid address
        args = ['address', 'delete', '1234']
        res = CommandWallet().execute(args)
        self.assertFalse(res)

        # test wallet delete address with unknown address
        args = ['address', 'delete', self.watch_addr_str]
        res = CommandWallet().execute(args)
        self.assertFalse(res)

        # test wallet delete successful
        self.assertTrue(len(PromptData.Wallet.Addresses), 1)
        args = ['address', 'delete', PromptData.Wallet.Addresses[0]]
        res = CommandWallet().execute(args)
        self.assertTrue(res)
        self.assertEqual(type(res), bool)
        self.assertEqual(len(PromptData.Wallet.Addresses), 0)

    def test_wallet_alias(self):
        # test wallet alias with no wallet open
        args = ['address', 'alias', 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3', 'mine']
        res = CommandWallet().execute(args)
        self.assertFalse(res)

        self.OpenWallet1()

        # test wallet alias with no argument
        args = ['address', 'alias']
        res = CommandWallet().execute(args)
        self.assertFalse(res)

        # test wallet alias with 1 argument
        args = ['address', 'alias', 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3']
        res = CommandWallet().execute(args)
        self.assertFalse(res)

        # test wallet alias successful
        self.assertNotIn('mine', [n.Title for n in PromptData.Wallet.NamedAddr])

        args = ['address', 'alias', 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3', 'mine']
        res = CommandWallet().execute(args)
        self.assertTrue(res)
        self.assertIn('mine', [n.Title for n in PromptData.Wallet.NamedAddr])

    def test_6_split_unspent(self):
        # os.environ["NEOPYTHON_UNITTEST"] = "1"
        wallet = self.GetWallet1(recreate=True)
        addr = wallet.ToScriptHash('AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3')

        # # bad inputs
        # tx = SplitUnspentCoin(None, self.NEO, addr, 0, 2)
        # self.assertEqual(tx, None)
        #
        # tx = SplitUnspentCoin(wallet, self.NEO, addr, 3, 2)
        # self.assertEqual(tx, None)
        #
        # tx = SplitUnspentCoin(wallet, 'bla', addr, 0, 2)
        # self.assertEqual(tx, None)

        # should be ok
        tx = SplitUnspentCoin(wallet, self.NEO, addr, 0, 2, prompt_passwd=False)
        self.assertIsNotNone(tx)

        # # rebuild wallet and try with non-even amount of neo, should be split into integer values of NEO
        # wallet = self.GetWallet1(True)
        # tx = SplitUnspentCoin(wallet, self.NEO, addr, 0, 3, prompt_passwd=False)
        # self.assertIsNotNone(tx)
        # self.assertEqual([Fixed8.FromDecimal(17), Fixed8.FromDecimal(17), Fixed8.FromDecimal(16)], [item.Value for item in tx.outputs])
        #
        # # try with gas
        # wallet = self.GetWallet1(True)
        # tx = SplitUnspentCoin(wallet, self.GAS, addr, 0, 3, prompt_passwd=False)
        # self.assertIsNotNone(tx)

    def test_7_create_address(self):
        # no wallet
        res = CreateAddress(None, 1)
        self.assertFalse(res)

        wallet = self.GetWallet1(recreate=True)

        # not specifying a number of addresses
        res = CreateAddress(wallet, None)
        self.assertFalse(res)

        # bad args
        res = CreateAddress(wallet, "blah")
        self.assertFalse(res)

        # negative value
        res = CreateAddress(wallet, -1)
        self.assertFalse(res)

        # should pass
        res = CreateAddress(wallet, 2)
        self.assertTrue(res)
        self.assertEqual(len(wallet.Addresses), 3)


class UserWalletSplitTestCase(UserWalletTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_wallet_split(self):
        # test wallet split with no wallet open
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['address', 'split']
            res = CommandWallet().execute(args)
            self.assertIsNone(res)
            self.assertIn("open a wallet", mock_print.getvalue())

        self.OpenWallet1()

        # test wallet split with not enough arguments
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['address', 'split', self.wallet_1_addr]
            res = CommandWallet().execute(args)
            self.assertIsNone(res)
            self.assertIn("specify the required parameters", mock_print.getvalue())

        # test wallet split with too much arguments
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['address', 'split', self.wallet_1_addr, 'neo', '0', '2', 'too', 'much']
            res = CommandWallet().execute(args)
            self.assertIsNone(res)
            self.assertIn("Too many parameters supplied", mock_print.getvalue())

        # test wallet split with invalid address
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['address', 'split', '123', 'neo', '0', '2']
            res = CommandWallet().execute(args)
            self.assertIsNone(res)
            self.assertIn("Invalid address specified", mock_print.getvalue())

        # test wallet split with unknown asset
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['address', 'split', self.wallet_1_addr, 'unknownasset', '0', '2']
            res = CommandWallet().execute(args)
            self.assertIsNone(res)
            self.assertIn("Unknown asset id", mock_print.getvalue())

        # test wallet split with invalid index
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['address', 'split', self.wallet_1_addr, 'neo', 'abc', '2']
            res = CommandWallet().execute(args)
            self.assertIsNone(res)
            self.assertIn("Invalid unspent index value", mock_print.getvalue())

        # test wallet split with invalid divisions
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['address', 'split', self.wallet_1_addr, 'neo', '0', 'abc']
            res = CommandWallet().execute(args)
            self.assertIsNone(res)
            self.assertIn("Invalid divisions value", mock_print.getvalue())

        # test wallet split with invalid divisions (negative)
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['address', 'split', self.wallet_1_addr, 'neo', '0', '-3']
            res = CommandWallet().execute(args)
            self.assertIsNone(res)
            self.assertIn("Divisions cannot be lower than 2", mock_print.getvalue())

        # test wallet split with invalid fee
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['address', 'split', self.wallet_1_addr, 'neo', '0', '2', 'abc']
            res = CommandWallet().execute(args)
            self.assertIsNone(res)
            self.assertIn("Invalid fee value", mock_print.getvalue())

        # test wallet split with negative fee
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['address', 'split', self.wallet_1_addr, 'neo', '0', '2', '-0.01']
            res = CommandWallet().execute(args)
            self.assertIsNone(res)
            self.assertIn("Invalid fee value", mock_print.getvalue())

        # test wallet split with wrong password
        with patch('neo.Prompt.Commands.WalletAddress.prompt', side_effect=["wrong_password"]):
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['address', 'split', self.wallet_1_addr, 'neo', '0', '2']
                res = CommandWallet().execute(args)
                self.assertIsNone(res)
                self.assertIn("incorrect password", mock_print.getvalue())

        # test wallet split with fee bigger than the outputs
        with patch('neo.Prompt.Commands.WalletAddress.prompt', side_effect=[self.wallet_1_pass()]):
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['address', 'split', self.wallet_1_addr, 'neo', '0', '2', '100']
                res = CommandWallet().execute(args)
                self.assertIsNone(res)
                self.assertIn("Fee could not be subtracted from outputs", mock_print.getvalue())

        # test wallet split with error during tx relay
        with patch('neo.Prompt.Commands.WalletAddress.prompt', side_effect=[self.wallet_1_pass()]):
            with patch('neo.Network.NodeLeader.NodeLeader.Relay', side_effect=[None]):
                with patch('sys.stdout', new=StringIO()) as mock_print:
                    args = ['address', 'split', self.wallet_1_addr, 'neo', '0', '2']
                    res = CommandWallet().execute(args)
                    self.assertIsNone(res)
                    self.assertIn("Could not relay tx", mock_print.getvalue())

        # test wallet split neo successful
        with patch('neo.Prompt.Commands.WalletAddress.prompt', side_effect=[self.wallet_1_pass()]):
            args = ['address', 'split', self.wallet_1_addr, 'neo', '0', '2']
            tx = CommandWallet().execute(args)
            self.assertTrue(tx)
            self.assertIsInstance(tx, ContractTransaction)
            self.assertEqual([Fixed8.FromDecimal(25), Fixed8.FromDecimal(25)], [item.Value for item in tx.outputs])

        # test wallet split gas successful
        with patch('neo.Prompt.Commands.WalletAddress.prompt', side_effect=[self.wallet_1_pass()]):
            args = ['address', 'split', self.wallet_1_addr, 'gas', '0', '3']
            tx = CommandWallet().execute(args)
            self.assertTrue(tx)
            self.assertIsInstance(tx, ContractTransaction)
            self.assertEqual(len(tx.outputs), 3)
