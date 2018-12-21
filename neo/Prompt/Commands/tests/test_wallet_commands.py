from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Wallets.utils import to_aes_key
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Core.Blockchain import Blockchain
from neocore.UInt160 import UInt160
from neocore.Fixed8 import Fixed8
from neo.Core.TX.ClaimTransaction import ClaimTransaction
from neo.Prompt.Commands.Wallet import CommandWallet
from neo.Prompt.Commands.Wallet import CreateAddress, DeleteAddress, ImportToken, ShowUnspentCoins, SplitUnspentCoin
from neo.Prompt.PromptData import PromptData
from contextlib import contextmanager
import os
import shutil
from mock import patch
from io import StringIO


class UserWalletTestCase(WalletFixtureTestCase):
    wallet_1_script_hash = UInt160(data=b'\x1c\xc9\xc0\\\xef\xff\xe6\xcd\xd7\xb1\x82\x81j\x91R\xec!\x8d.\xc0')
    wallet_1_addr = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'
    _wallet1 = None

    wallet_2_script_hash = UInt160(data=b'\x08t/\\P5\xac-\x0b\x1c\xb4\x94tIyBu\x7f1*')
    wallet_2_addr = 'AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEm'
    _wallet2 = None

    import_watch_addr = UInt160(data=b'\x08t/\\P5\xac-\x0b\x1c\xb4\x94tIyBu\x7f1*')
    watch_addr_str = 'AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEm'

    @property
    def GAS(self):
        return Blockchain.Default().SystemCoin().Hash

    @property
    def NEO(self):
        return Blockchain.Default().SystemShare().Hash

    @classmethod
    def GetWallet1(cls, recreate=False):
        if cls._wallet1 is None or recreate:
            shutil.copyfile(cls.wallet_1_path(), cls.wallet_1_dest())
            cls._wallet1 = UserWallet.Open(UserWalletTestCase.wallet_1_dest(),
                                           to_aes_key(UserWalletTestCase.wallet_1_pass()))
        return cls._wallet1

    @classmethod
    def GetWallet2(cls, recreate=False):
        if cls._wallet2 is None or recreate:
            shutil.copyfile(cls.wallet_2_path(), cls.wallet_2_dest())
            cls._wallet2 = UserWallet.Open(UserWalletTestCase.wallet_2_dest(),
                                           to_aes_key(UserWalletTestCase.wallet_2_pass()))
        return cls._wallet2

    @classmethod
    def OpenWallet1(cls):
        PromptData.Wallet = cls.GetWallet1(recreate=True)

    @classmethod
    def OpenWallet2(cls):
        PromptData.Wallet = cls.GetWallet2(recreate=True)

    @classmethod
    def tearDown(cls):
        PromptData.Wallet = None

    # Beginning with refactored tests

    def test_wallet(self):
        # without wallet opened
        res = CommandWallet().execute(None)
        self.assertFalse(res)

        # with wallet opened
        self.OpenWallet1()
        res = CommandWallet().execute(None)
        self.assertEqual(type(res), UserWallet)

    def test_wallet_wrong_command(self):
        self.OpenWallet1()
        args = ['badcommand']
        res = CommandWallet().execute(args)
        self.assertFalse(res)

    def test_wallet_create(self):
        def remove_new_wallet():
            path = UserWalletTestCase.new_wallet_dest()
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                print("couldn't remove wallets %s " % e)

        with patch('neo.Prompt.PromptData.PromptData.Prompt'):
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=["testpassword", "testpassword"]):
                # test wallet create successful
                path = UserWalletTestCase.new_wallet_dest()
                args = ['create', path]
                self.assertFalse(os.path.isfile(path))
                res = CommandWallet().execute(args)
                self.assertEqual(type(res), UserWallet)
                self.assertTrue(os.path.isfile(path))
                remove_new_wallet()

            # test wallet create with no path
            args = ['create']
            res = CommandWallet().execute(args)
            self.assertFalse(res)

            # test wallet open with already existing path
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=["testpassword", "testpassword"]):
                path = UserWalletTestCase.new_wallet_dest()
                args = ['create', path]
                self.assertFalse(os.path.isfile(path))
                res = CommandWallet().execute(args)
                self.assertEqual(type(res), UserWallet)
                self.assertTrue(os.path.isfile(path))

                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertTrue(os.path.isfile(path))
                remove_new_wallet()

            # test wallet with different passwords
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=["testpassword", "bad"]):
                path = UserWalletTestCase.new_wallet_dest()
                args = ['create', path]
                self.assertFalse(os.path.isfile(path))
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertFalse(os.path.isfile(path))

            # test wallet create unsuccessful
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=["testpassword", "testpassword"]):
                with patch('neo.Implementations.Wallets.peewee.UserWallet.UserWallet.Create', side_effect=[Exception('test exception')]):
                    path = UserWalletTestCase.new_wallet_dest()
                    args = ['create', path]
                    res = CommandWallet().execute(args)
                    self.assertFalse(res)
                    self.assertFalse(os.path.isfile(path))

            # test wallet create exception after creation
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=["testpassword", "testpassword"]):
                with patch('neo.Wallets.Wallet.Wallet.GetKey', side_effect=[Exception('test exception')]):
                    path = UserWalletTestCase.new_wallet_dest()
                    args = ['create', path]
                    res = CommandWallet().execute(args)
                    self.assertFalse(res)
                    self.assertFalse(os.path.isfile(path))

            # test wallet create exception after creation with file deletion failure
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=["testpassword", "testpassword"]):
                with patch('neo.Wallets.Wallet.Wallet.GetKey', side_effect=[Exception('test exception')]):
                    with patch('os.remove', side_effect=[Exception('test exception')]):
                        path = UserWalletTestCase.new_wallet_dest()
                        args = ['create', path]
                        res = CommandWallet().execute(args)
                        self.assertFalse(res)
                        self.assertTrue(os.path.isfile(path))
                    remove_new_wallet()

    def test_wallet_open(self):
        with patch('neo.Prompt.PromptData.PromptData.Prompt'):
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=[self.wallet_1_pass()]):
                if self._wallet1 is None:
                    shutil.copyfile(self.wallet_1_path(), self.wallet_1_dest())

                # test wallet open successful
                args = ['open', self.wallet_1_dest()]

                res = CommandWallet().execute(args)

                self.assertEqual(type(res), UserWallet)

            # test wallet open with no path; this will also close the open wallet
            args = ['open']

            res = CommandWallet().execute(args)

            self.assertFalse(res)

            # test wallet open with bad path
            args = ['open', 'badpath']

            res = CommandWallet().execute(args)

            self.assertFalse(res)

        # test wallet open unsuccessful
        with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=["testpassword"]):
            with patch('neo.Implementations.Wallets.peewee.UserWallet.UserWallet.Open', side_effect=[Exception('test exception')]):
                args = ['open', 'fixtures/testwallet.db3']

                res = CommandWallet().execute(args)

                self.assertFalse(res)

    def test_wallet_close(self):
        with patch('neo.Prompt.PromptData.PromptData.Prompt'):
            # test wallet close with no wallet
            args = ['close']

            res = CommandWallet().execute(args)

            self.assertFalse(res)

            # test wallet close with open wallet
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=[self.wallet_1_pass()]):
                if self._wallet1 is None:
                    shutil.copyfile(self.wallet_1_path(), self.wallet_1_dest())

                args = ['open', self.wallet_1_dest()]

                res = CommandWallet().execute(args)

                self.assertEqual(type(res), UserWallet)

                # now close the open wallet manually
                args = ['close']

                res = CommandWallet().execute(args)

                self.assertTrue(res)

    def test_wallet_verbose(self):
        # test wallet verbose with no wallet opened
        args = ['verbose']
        res = CommandWallet().execute(args)
        self.assertFalse(res)

        self.OpenWallet1()

        # test wallet close with open wallet
        args = ['verbose']
        res = CommandWallet().execute(args)
        self.assertTrue(res)

    def test_wallet_create_address(self):
        # test wallet create address with no wallet open
        args = ['create_addr', 1]
        res = CommandWallet().execute(args)
        self.assertFalse(res)

        self.OpenWallet1()

        # test wallet create address with no argument
        args = ['create_addr']
        res = CommandWallet().execute(args)
        self.assertFalse(res)

        # test wallet create address with negative number
        args = ['create_addr', -1]
        res = CommandWallet().execute(args)
        self.assertFalse(res)

        # test wallet create address successful
        args = ['create_addr', 1]
        res = CommandWallet().execute(args)
        self.assertTrue(res)
        self.assertEqual(type(res), UserWallet)
        self.assertEqual(len(res.Addresses), 2)  # Has one address when created.

        args = ['create_addr', 7]
        res = CommandWallet().execute(args)
        self.assertTrue(res)
        self.assertEqual(type(res), UserWallet)
        self.assertEqual(len(res.Addresses), 9)

    def test_wallet_delete_address(self):
        # test wallet delete address with no wallet open
        args = ['delete_addr']
        res = CommandWallet().execute(args)
        self.assertFalse(res)

        self.OpenWallet1()

        # test wallet delete address with no argument
        args = ['delete_addr']
        res = CommandWallet().execute(args)
        self.assertFalse(res)

        # test wallet delete address with invalid address
        args = ['delete_addr', '1234']
        res = CommandWallet().execute(args)
        self.assertFalse(res)

        # test wallet delete address with unknown address
        args = ['delete_addr', self.watch_addr_str]
        res = CommandWallet().execute(args)
        self.assertFalse(res)

        # test wallet delete successful
        self.assertTrue(len(PromptData.Wallet.Addresses), 1)
        args = ['delete_addr', PromptData.Wallet.Addresses[0]]
        res = CommandWallet().execute(args)
        self.assertTrue(res)
        self.assertEqual(type(res), bool)
        self.assertEqual(len(PromptData.Wallet.Addresses), 0)

    def test_wallet_claim_1(self):
        # test with no wallet
        args = ['claim']
        res = CommandWallet().execute(args)
        self.assertFalse(res)

        self.OpenWallet1()

        # test wrong password
        with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=["wrong"]):
            args = ['claim']
            claim_tx, relayed = CommandWallet().execute(args)
            self.assertEqual(claim_tx, None)
            self.assertFalse(relayed)

        # test successfull
        with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=[WalletFixtureTestCase.wallet_1_pass()]):
            args = ['claim']
            claim_tx, relayed = CommandWallet().execute(args)
            self.assertIsInstance(claim_tx, ClaimTransaction)
            self.assertTrue(relayed)

        # test nothing to claim anymore
        with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=[WalletFixtureTestCase.wallet_1_pass()]):
            args = ['claim']
            claim_tx, relayed = CommandWallet().execute(args)
            self.assertEqual(claim_tx, None)
            self.assertFalse(relayed)

    def test_wallet_claim_2(self):
        self.OpenWallet2()

        # test with --from-addr
        with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=[WalletFixtureTestCase.wallet_2_pass()]):
            args = ['claim', '--from-addr=AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3']
            claim_tx, relayed = CommandWallet().execute(args)
            self.assertIsInstance(claim_tx, ClaimTransaction)
            self.assertTrue(relayed)

            json_tx = claim_tx.ToJson()
            self.assertEqual(json_tx['vout'][0]['address'], 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3')

    def test_wallet_rebuild(self):
        with patch('neo.Prompt.PromptData.PromptData.Prompt'):
            # test wallet rebuild with no wallet open
            args = ['rebuild']
            res = CommandWallet().execute(args)
            self.assertFalse(res)

            self.OpenWallet1()
            PromptData.Wallet._current_height = 12345

            # test wallet rebuild with no argument
            args = ['rebuild']
            CommandWallet().execute(args)
            self.assertEqual(PromptData.Wallet._current_height, 0)

            # test wallet rebuild with start block
            args = ['rebuild', '42']
            CommandWallet().execute(args)
            self.assertEqual(PromptData.Wallet._current_height, 42)

    def test_wallet_alias(self):
        # test wallet alias with no wallet open
        args = ['alias', 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3', 'mine']
        res = CommandWallet().execute(args)
        self.assertFalse(res)

        self.OpenWallet1()

        # test wallet alias with no argument
        args = ['alias']
        res = CommandWallet().execute(args)
        self.assertFalse(res)

        # test wallet alias with 1 argument
        args = ['alias', 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3']
        res = CommandWallet().execute(args)
        self.assertFalse(res)

        # test wallet alias successful
        self.assertNotIn('mine', [n.Title for n in PromptData.Wallet.NamedAddr])

        args = ['alias', 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3', 'mine']
        res = CommandWallet().execute(args)
        self.assertTrue(res)
        self.assertIn('mine', [n.Title for n in PromptData.Wallet.NamedAddr])

    ##########################################################
    ##########################################################

    def test_3_import_token(self):
        wallet = self.GetWallet1(recreate=True)

        self.assertEqual(len(wallet.GetTokens()), 1)

        token_hash = '31730cc9a1844891a3bafd1aa929a4142860d8d3'

        ImportToken(wallet, token_hash)

        token = list(wallet.GetTokens().values())[0]

        self.assertEqual(token.name, 'NEX Template V4')
        self.assertEqual(token.symbol, 'NXT4')
        self.assertEqual(token.decimals, 8)
        self.assertEqual(token.Address, 'Ab61S1rk2VtCVd3NtGNphmBckWk4cfBdmB')

    def test_4_get_synced_balances(self):
        wallet = self.GetWallet1(recreate=True)
        synced_balances = wallet.GetSyncedBalances()
        self.assertEqual(len(synced_balances), 2)

    def test_5_show_unspent(self):
        wallet = self.GetWallet1(recreate=True)
        unspents = ShowUnspentCoins(wallet, [])
        self.assertEqual(len(unspents), 2)

        unspents = ShowUnspentCoins(wallet, ['neo'])
        self.assertEqual(len(unspents), 1)

        unspents = ShowUnspentCoins(wallet, ['gas'])
        self.assertEqual(len(unspents), 1)

        unspents = ShowUnspentCoins(wallet, ['AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'])
        self.assertEqual(len(unspents), 2)

        unspents = ShowUnspentCoins(wallet, ['AYhE3Svuqdfh1RtzvE8hUhNR7HSpaSDFQg'])
        self.assertEqual(len(unspents), 0)

        unspents = ShowUnspentCoins(wallet, ['--watch'])
        self.assertEqual(len(unspents), 0)

    def test_6_split_unspent(self):
        wallet = self.GetWallet1(recreate=True)

        # test bad
        tx = SplitUnspentCoin(wallet, [])
        self.assertEqual(tx, None)

        # bad inputs
        tx = SplitUnspentCoin(wallet, ['AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3', 'neo', 3, 2])
        self.assertEqual(tx, None)

        # should be ok
        tx = SplitUnspentCoin(wallet, ['AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3', 'neo', 0, 2], prompt_passwd=False)
        self.assertIsNotNone(tx)

        # rebuild wallet and try with non-even amount of neo, should be split into integer values of NEO
        wallet = self.GetWallet1(True)
        tx = SplitUnspentCoin(wallet, ['AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3', 'neo', 0, 3], prompt_passwd=False)
        self.assertIsNotNone(tx)

        self.assertEqual([Fixed8.FromDecimal(17), Fixed8.FromDecimal(17), Fixed8.FromDecimal(16)], [item.Value for item in tx.outputs])

        # try with gas
        wallet = self.GetWallet1(True)
        tx = SplitUnspentCoin(wallet, ['AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3', 'gas', 0, 3], prompt_passwd=False)
        self.assertIsNotNone(tx)

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

    def test_wallet_export_baseclass(self):
        self.OpenWallet1()

        # test with no argument
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['export']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Please specify an action", mock_print.getvalue())

        # test with an invalid action
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['export', 'bad_action']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("is an invalid parameter", mock_print.getvalue())

        # test with a good action
        with patch('neo.Prompt.Commands.Wallet.CommandWalletExport.execute_sub_command', side_effect=[True]):
            args = ['export', 'mocked_action']
            res = CommandWallet().execute(args)
            self.assertTrue(res)

    def test_wallet_export_wif(self):
        self.OpenWallet1()
        # test missing address argument
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['export', 'wif']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("specify the required parameter", mock_print.getvalue())

        # test with an address that's not part of the wallet
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['export', 'wif', 'bad_address']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Could not find address", mock_print.getvalue())

        # test with good address
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['export', 'wif', self.wallet_1_addr]
            res = CommandWallet().execute(args)
            self.assertTrue(res)
            self.assertIn("Ky94Rq8rb1z8UzTthYmy1ApbZa9xsKTvQCiuGUZJZbaDJZdkvLRV", mock_print.getvalue())

    def test_wallet_export_nep2(self):
        self.OpenWallet1()
        # test missing address argument
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['export', 'nep2']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("specify the required parameter", mock_print.getvalue())

        # test with non matching passwords
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=['random_passw', 'random_wrong_second_passw']):
                args = ['export', 'nep2', 'bad_address']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("Please provide matching passwords", mock_print.getvalue())

        # test with an address that's not part of the wallet
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=['random_passw', 'random_passw']):
                args = ['export', 'nep2', 'bad_address']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("Could not find address", mock_print.getvalue())

        # test with good address and but too short passphrase
        with patch('sys.stdout', new=StringIO()) as mock_print:
            pw_too_short = 'too_short'
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=[pw_too_short, pw_too_short]):
                args = ['export', 'nep2', self.wallet_1_addr]
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("Passphrase is too short", mock_print.getvalue())

        # test with good address and good passphrase len
        with patch('sys.stdout', new=StringIO()) as mock_print:
            pw = UserWalletTestCase.wallet_1_pass()
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=[pw, pw]):
                args = ['export', 'nep2', self.wallet_1_addr]
                res = CommandWallet().execute(args)
                self.assertTrue(res)
                self.assertIn("6PYK1E3skTFLgtsnVNKDCEdUQxeKbRmKBnbkPFxvGGggfeB2JacnMpqkcH", mock_print.getvalue())

    def test_wallet_import_baseclass(self):
        self.OpenWallet1()

        # test with no argument
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Please specify an action", mock_print.getvalue())

        # test with an invalid action
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'bad_action']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("is an invalid parameter", mock_print.getvalue())

        # test with a good action
        with patch('neo.Prompt.Commands.Wallet.CommandWalletImport.execute_sub_command', side_effect=[True]):
            args = ['import', 'mocked_action']
            res = CommandWallet().execute(args)
            self.assertTrue(res)

    def test_wallet_import_wif(self):
        self.OpenWallet1()

        # test missing wif key argument
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'wif']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("specify the required parameter", mock_print.getvalue())

        # test with bad wif length
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'wif', 'too_short']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Please provide a wif with a length of 52 bytes", mock_print.getvalue())

        # test with invalid wif
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'wif', 'a' * 52]
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Invalid format", mock_print.getvalue())

        # test with exception in key creation
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Wallet.PromptData.Wallet.CreateKey', side_effect=[Exception("unittest_error")]):
                with self.assertRaises(Exception) as context:
                    args = ['import', 'wif', 'Ky94Rq8rb1z8UzTthYmy1ApbZa9xsKTvQCiuGUZJZbaDJZdkvLRV']
                    res = CommandWallet().execute(args)
                    self.assertFalse(res)
                    self.assertIn("unittest_error", str(context.exception))
                    self.assertIn("unittest_error", mock_print.getvalue())

        # test with valid wif
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'wif', 'Ky94Rq8rb1z8UzTthYmy1ApbZa9xsKTvQCiuGUZJZbaDJZdkvLRV']
            res = CommandWallet().execute(args)
            self.assertTrue(res)
            self.assertIn(self.wallet_1_addr, mock_print.getvalue())

    def test_wallet_import_nep2(self):
        self.OpenWallet1()

        # test missing nep2 key argument
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'nep2']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("specify the required parameter", mock_print.getvalue())

        # test with bad nep2 length
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=['random_passw']):
                args = ['import', 'nep2', 'too_short_nep2_key']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("Please provide a nep2_key with a length of 58 bytes", mock_print.getvalue())

        # test with ok NEP2, bad password
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=['wrong_password']):
                args = ['import', 'nep2', '6PYK1E3skTFLgtsnVNKDCEdUQxeKbRmKBnbkPFxvGGggfeB2JacnMpqkcH']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("Wrong passphrase", mock_print.getvalue())

        # test with exception in key creation
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
                with patch('neo.Prompt.Commands.Wallet.PromptData.Wallet.CreateKey', side_effect=[Exception("unittest_error")]):
                    args = ['import', 'nep2', '6PYK1E3skTFLgtsnVNKDCEdUQxeKbRmKBnbkPFxvGGggfeB2JacnMpqkcH']
                    res = CommandWallet().execute(args)
                    self.assertFalse(res)
                    self.assertIn("Key creation error", mock_print.getvalue())
                    self.assertIn("unittest_error", mock_print.getvalue())

        # test with ok
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
                args = ['import', 'nep2', '6PYK1E3skTFLgtsnVNKDCEdUQxeKbRmKBnbkPFxvGGggfeB2JacnMpqkcH']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                # if we imported successfully we get the wallet1 address
                self.assertIn(self.wallet_1_addr, mock_print.getvalue())

    def test_wallet_import_watchaddr(self):
        self.OpenWallet1()

        # test missing wif key argument
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'watch_addr']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("specify the required parameter", mock_print.getvalue())

        # test with bad address
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'watch_addr', 'too_short_addr']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Invalid address specified", mock_print.getvalue())

        # test with good address
        with patch('sys.stdout', new=StringIO()) as mock_print:
            address = 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg'
            args = ['import', 'watch_addr', address]
            res = CommandWallet().execute(args)
            self.assertTrue(res)
            self.assertIn("Added address", mock_print.getvalue())
            self.assertIn("watch-only", mock_print.getvalue())
            self.assertIn(PromptData.Wallet.ToScriptHash(address), PromptData.Wallet.LoadWatchOnly())

        # test address already exists
        with patch('sys.stdout', new=StringIO()) as mock_print:
            address = 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg'
            args = ['import', 'watch_addr', address]
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Address already exists in wallet", mock_print.getvalue())

    def test_wallet_import_multisig_address(self):
        self.OpenWallet1()

        # test missing all arguments
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'multisig_addr']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Please specify the minimum required parameters", mock_print.getvalue())

        # test invalid public key format
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'multisig_addr', 'not_a_public_key', 'arg2', 'arg3']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Invalid public key format", mock_print.getvalue())

        # test invalid public key format 2 (fail to convert to UIn160)
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'multisig_addr', 'Å' * 66, 'arg2', 'arg3']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Invalid public key format", mock_print.getvalue())

        # test with a public key not present in our own wallet
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'multisig_addr', '031a6c6fbbdf02ca351745fa86b9ba5a9452d785ac4f7fc2b7548ca2a46c4fcf4a', 'arg2', 'arg3']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Supplied first public key does not exist in own wallet", mock_print.getvalue())

        # test with bad minimum signature value 1
        with patch('sys.stdout', new=StringIO()) as mock_print:
            # 0 not allowed
            args = ['import', 'multisig_addr', '03cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6', '0', 'arg3']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Minimum signatures count cannot be lower than 1", mock_print.getvalue())

        # test with bad minimum signature value 2
        with patch('sys.stdout', new=StringIO()) as mock_print:
            # 'bla' is not a valid int
            args = ['import', 'multisig_addr', '03cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6', 'bla', 'arg3']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Invalid minimum signature count value", mock_print.getvalue())

        # test with insufficient remaining signing keys
        with patch('sys.stdout', new=StringIO()) as mock_print:
            # 0 not allowed
            args = ['import', 'multisig_addr', '03cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6', '2', 'key1']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Minimum required: 2 given: 1", mock_print.getvalue())

        # test with bad remaining signing key 1
        with patch('sys.stdout', new=StringIO()) as mock_print:
            # 0 not allowed
            args = ['import', 'multisig_addr', '03cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6', '1', 'too_short_signing_key']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Invalid signing key", mock_print.getvalue())

        # test with non unique signing keys
        with patch('sys.stdout', new=StringIO()) as mock_print:
            # 0 not allowed
            args = ['import', 'multisig_addr', '03cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6', '1',
                    '03cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Provided signing keys are not unique", mock_print.getvalue())

        # test with all good \o/
        with patch('sys.stdout', new=StringIO()) as mock_print:
            # 0 not allowed
            args = ['import', 'multisig_addr', '03cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6', '1',
                    '031a6c6fbbdf02ca351745fa86b9ba5a9452d785ac4f7fc2b7548ca2a46c4fcf4a']
            res = CommandWallet().execute(args)
            self.assertTrue(res)
            self.assertIn("Added multi-sig contract address", mock_print.getvalue())
