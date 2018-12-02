from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Wallets.utils import to_aes_key
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Core.Blockchain import Blockchain
from neocore.UInt160 import UInt160
from neocore.Fixed8 import Fixed8
from neo.Prompt.Commands.Wallet import CommandWallet, CreateAddress, DeleteAddress, ImportToken, ImportWatchAddr, ShowUnspentCoins, SplitUnspentCoin
from neo.Prompt.PromptData import PromptData
import os
import shutil
from mock import patch


class UserWalletTestCase(WalletFixtureTestCase):
    wallet_1_script_hash = UInt160(data=b'\x1c\xc9\xc0\\\xef\xff\xe6\xcd\xd7\xb1\x82\x81j\x91R\xec!\x8d.\xc0')

    wallet_1_addr = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'

    import_watch_addr = UInt160(data=b'\x08t/\\P5\xac-\x0b\x1c\xb4\x94tIyBu\x7f1*')
    watch_addr_str = 'AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEm'
    _wallet1 = None

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
    def OpenWallet(cls):
        PromptData.Wallet = cls.GetWallet1(recreate=True)

    @classmethod
    def tearDown(cls):
        PromptData.Wallet = None

    # Beginning with refactored tests

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
                self.assertEqual(str(type(res)), "<class 'neo.Implementations.Wallets.peewee.UserWallet.UserWallet'>")
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
                self.assertEqual(str(type(res)), "<class 'neo.Implementations.Wallets.peewee.UserWallet.UserWallet'>")
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

    def test_wallet_open(self):
        with patch('neo.Prompt.PromptData.PromptData.Prompt'):
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=["testpassword"]):
                # test wallet open successful
                args = ['open', 'fixtures/testwallet.db3']

                res = CommandWallet().execute(args)

                self.assertEqual(str(type(res)), "<class 'neo.Implementations.Wallets.peewee.UserWallet.UserWallet'>")

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
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=["testpassword"]):
                args = ['open', 'fixtures/testwallet.db3']

                res = CommandWallet().execute(args)

                self.assertEqual(str(type(res)), "<class 'neo.Implementations.Wallets.peewee.UserWallet.UserWallet'>")

                # now close the open wallet manually
                args = ['close']

                res = CommandWallet().execute(args)

                self.assertTrue(res)

    def test_wallet_verbose(self):
        with patch('neo.Prompt.PromptData.PromptData.Prompt'):
            # test wallet verbose with no wallet
            args = ['verbose']
            res = CommandWallet().execute(args)
            self.assertFalse(res)

        # test wallet close with open wallet
        self.OpenWallet()
        args = ['verbose']
        res = CommandWallet().execute(args)
        self.assertTrue(res)

    def test_wallet_migrate(self):
        pass

    def test_wallet_create_address(self):
        with patch('neo.Prompt.PromptData.PromptData.Prompt'):
            # test wallet create address with no wallet open
            args = ['create_addr', 1]
            res = CommandWallet().execute(args)
            self.assertFalse(res)

            self.OpenWallet()

            # test wallet create address with no argument
            args = ['create_addr']
            res = CommandWallet().execute(args)
            self.assertFalse(res)

            # test wallet create address with negative number
            args = ['create_addr', -1]
            res = CommandWallet().execute(args)
            self.assertFalse(res)

            # test wallet create successful
            args = ['create_addr', 1]
            res = CommandWallet().execute(args)
            self.assertTrue(res)
            self.assertEqual(str(type(res)), "<class 'neo.Implementations.Wallets.peewee.UserWallet.UserWallet'>")
            self.assertEqual(len(res.Addresses), 2)  # Has one address when created.

            args = ['create_addr', 7]
            res = CommandWallet().execute(args)
            self.assertTrue(res)
            self.assertEqual(str(type(res)), "<class 'neo.Implementations.Wallets.peewee.UserWallet.UserWallet'>")
            self.assertEqual(len(res.Addresses), 9)

    ##########################################################
    ##########################################################
    def test_1_import_addr(self):
        wallet = self.GetWallet1(recreate=True)

        self.assertEqual(len(wallet.LoadWatchOnly()), 0)

        result = ImportWatchAddr(wallet, self.watch_addr_str)

        self.assertEqual(len(wallet.LoadWatchOnly()), 1)

    def test_2_import_addr(self):
        wallet = self.GetWallet1()

        self.assertEqual(len(wallet.LoadWatchOnly()), 1)

        success = DeleteAddress(wallet, self.watch_addr_str)

        self.assertTrue(success)

        self.assertEqual(len(wallet.LoadWatchOnly()), 0)

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
