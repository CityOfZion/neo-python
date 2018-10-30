from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Wallets.utils import to_aes_key
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Core.Blockchain import Blockchain
from neocore.UInt160 import UInt160
from neocore.Fixed8 import Fixed8
from neo.Prompt.Commands.Wallet import CreateAddress, DeleteAddress, ImportToken, ImportWatchAddr, ShowUnspentCoins, SplitUnspentCoin
import shutil


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
