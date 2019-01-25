from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Wallets.utils import to_aes_key
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Core.Blockchain import Blockchain
from neocore.UInt160 import UInt160
from neo.Core.TX.ClaimTransaction import ClaimTransaction
from neo.Prompt.Commands.Wallet import CommandWallet
from neo.Prompt.Commands.Wallet import ShowUnspentCoins
from neo.Prompt.PromptData import PromptData
from neo.Prompt.PromptPrinter import pp
import os
import shutil
from mock import patch
from io import StringIO


class UserWalletTestCaseBase(WalletFixtureTestCase):
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


class UserWalletTestCase(UserWalletTestCaseBase):
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

    def test_wallet_claim_1(self):
        # test with no wallet
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['claim']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Please open a wallet", mock_print.getvalue())

        self.OpenWallet1()

        # test wrong password
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=["wrong"]):
                args = ['claim']
                claim_tx, relayed = CommandWallet().execute(args)
                self.assertEqual(claim_tx, None)
                self.assertFalse(relayed)
                self.assertIn("Incorrect password", mock_print.getvalue())

        # test successful
        with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=[WalletFixtureTestCase.wallet_1_pass()]):
            args = ['claim']
            claim_tx, relayed = CommandWallet().execute(args)
            self.assertIsInstance(claim_tx, ClaimTransaction)
            self.assertTrue(relayed)

            json_tx = claim_tx.ToJson()
            self.assertEqual(json_tx['vout'][0]['address'], self.wallet_1_addr)

        # test nothing to claim anymore
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=[WalletFixtureTestCase.wallet_1_pass()]):
                args = ['claim']
                claim_tx, relayed = CommandWallet().execute(args)
                self.assertEqual(claim_tx, None)
                self.assertFalse(relayed)
                self.assertIn("No claims to process", mock_print.getvalue())

    def test_wallet_claim_2(self):
        self.OpenWallet2()

        # test with bad --from-addr
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=[WalletFixtureTestCase.wallet_2_pass()]):
                args = ['claim', '--from-addr=AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc']  # address is too short
                claim_tx, relayed = CommandWallet().execute(args)
                self.assertEqual(claim_tx, None)
                self.assertFalse(relayed)
                self.assertIn("Not correct Address, wrong length.", mock_print.getvalue())

        # test with invalid --from-addr
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=[WalletFixtureTestCase.wallet_2_pass()]):
                args = ['claim', '--from-addr=VJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3']  # address does not start with 'A'
                claim_tx, relayed = CommandWallet().execute(args)
                self.assertEqual(claim_tx, None)
                self.assertFalse(relayed)
                self.assertIn("Address format error", mock_print.getvalue())

        # successful test with --from-addr
        with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=[WalletFixtureTestCase.wallet_2_pass()]):
            args = ['claim', '--from-addr=' + self.wallet_1_addr]
            claim_tx, relayed = CommandWallet().execute(args)
            self.assertIsInstance(claim_tx, ClaimTransaction)
            self.assertTrue(relayed)

            json_tx = claim_tx.ToJson()
            self.assertEqual(json_tx['vout'][0]['address'], self.wallet_1_addr)

    def test_wallet_claim_3(self):
        self.OpenWallet1()

        # test with bad --to-addr
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=[WalletFixtureTestCase.wallet_1_pass()]):
                args = ['claim', '--to-addr=AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEn']  # bad address checksum
                claim_tx, relayed = CommandWallet().execute(args)
                self.assertEqual(claim_tx, None)
                self.assertFalse(relayed)
                self.assertIn("Address format error", mock_print.getvalue())

        # test with an invalid --to-addr
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=[WalletFixtureTestCase.wallet_1_pass()]):
                args = ['claim', '--to-addr=blah']  # completely wrong address format
                claim_tx, relayed = CommandWallet().execute(args)
                self.assertEqual(claim_tx, None)
                self.assertFalse(relayed)
                self.assertIn("Not correct Address, wrong length", mock_print.getvalue())

        # test with --to-addr
        with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=[WalletFixtureTestCase.wallet_1_pass()]):
            args = ['claim', '--to-addr=' + self.watch_addr_str]
            claim_tx, relayed = CommandWallet().execute(args)
            self.assertIsInstance(claim_tx, ClaimTransaction)
            self.assertTrue(relayed)

            json_tx = claim_tx.ToJson()
            self.assertEqual(json_tx['vout'][0]['address'], self.watch_addr_str)  # note how the --to-addr supercedes the default change address

    def test_wallet_claim_4(self):
        self.OpenWallet2()

        # test with --from-addr and --to-addr
        with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=[WalletFixtureTestCase.wallet_2_pass()]):
            args = ['claim', '--from-addr=' + self.wallet_1_addr, '--to-addr=' + self.wallet_2_addr]
            claim_tx, relayed = CommandWallet().execute(args)
            self.assertIsInstance(claim_tx, ClaimTransaction)
            self.assertTrue(relayed)

            json_tx = claim_tx.ToJson()
            self.assertEqual(json_tx['vout'][0]['address'], self.wallet_2_addr)  # note how the --to-addr also supercedes the from address if both are specified

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

    def test_wallet_unspent(self):
        # test wallet unspent with no wallet open
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['unspent']
            res = CommandWallet().execute(args)
            self.assertIsNone(res)
            self.assertIn("open a wallet", mock_print.getvalue())

        self.OpenWallet1()

        # test wallet unspent with invalid address
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['unspent', '--from-addr=123']
            res = CommandWallet().execute(args)
            self.assertIsNone(res)
            self.assertIn("Invalid address specified", mock_print.getvalue())

        # test wallet unspent successful
        args = ['unspent']
        res = CommandWallet().execute(args)
        self.assertTrue(res)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].Output.AssetId, self.NEO)
        self.assertEqual(res[1].Output.AssetId, self.GAS)

        # test wallet unspent with unknown asset shows all
        args = ['unspent', 'unknownasset']
        res = CommandWallet().execute(args)
        self.assertTrue(res)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].Output.AssetId, self.NEO)
        self.assertEqual(res[1].Output.AssetId, self.GAS)

        # test wallet unspent with asset
        args = ['unspent', 'neo']
        res = CommandWallet().execute(args)
        self.assertTrue(res)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].Output.AssetId, self.NEO)

        # test wallet unspent with asset
        args = ['unspent', 'gas']
        res = CommandWallet().execute(args)
        self.assertTrue(res)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].Output.AssetId, self.GAS)

        # test wallet unspent with unrelated address
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['unspent', '--from-addr=AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEm']
            res = CommandWallet().execute(args)
            self.assertEqual(res, [])
            self.assertIn("No unspent assets matching the arguments", mock_print.getvalue())

        # test wallet unspent with address
        args = ['unspent', '--from-addr=AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3']
        res = CommandWallet().execute(args)
        self.assertTrue(res)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].Output.AssetId, self.NEO)
        self.assertEqual(res[1].Output.AssetId, self.GAS)

        # test wallet unspent with --watch
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['unspent', '--watch']
            res = CommandWallet().execute(args)
            self.assertEqual(res, [])
            self.assertIn("No unspent assets matching the arguments", mock_print.getvalue())

        # test wallet unspent with --count
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['unspent', '--count']
            res = CommandWallet().execute(args)
            self.assertEqual(len(res), 2)
            self.assertIn("Total Unspent: 2", mock_print.getvalue())

        # test wallet unspent with --count
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['unspent', 'gas', '--count']
            res = CommandWallet().execute(args)
            self.assertEqual(len(res), 1)
            self.assertIn("Total Unspent: 1", mock_print.getvalue())

    ##########################################################
    ##########################################################

    def test_4_get_synced_balances(self):
        wallet = self.GetWallet1(recreate=True)
        synced_balances = wallet.GetSyncedBalances()
        self.assertEqual(len(synced_balances), 2)

    def test_5_show_unspent(self):
        wallet = self.GetWallet1(recreate=True)
        unspents = ShowUnspentCoins(wallet)
        self.assertEqual(len(unspents), 2)

        unspents = ShowUnspentCoins(wallet, asset_id=self.NEO)
        self.assertEqual(len(unspents), 1)

        unspents = ShowUnspentCoins(wallet, asset_id=self.GAS)
        self.assertEqual(len(unspents), 1)

        unspents = ShowUnspentCoins(wallet, from_addr=wallet.ToScriptHash('AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'))
        self.assertEqual(len(unspents), 2)

        unspents = ShowUnspentCoins(wallet, from_addr=wallet.ToScriptHash('AYhE3Svuqdfh1RtzvE8hUhNR7HSpaSDFQg'))
        self.assertEqual(len(unspents), 0)

        unspents = ShowUnspentCoins(wallet, watch_only=True)
        self.assertEqual(len(unspents), 0)
