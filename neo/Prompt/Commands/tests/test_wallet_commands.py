from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Wallets.utils import to_aes_key
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Core.Blockchain import Blockchain
from neocore.UInt160 import UInt160
from neocore.Fixed8 import Fixed8
from neo.Prompt.Commands.Wallet import DeleteAddress, ImportToken, ImportWatchAddr, ShowUnspentCoins, SplitUnspentCoin
import shutil


class UserWalletTestCase(WalletFixtureTestCase):

    wallet_1_script_hash = UInt160(data=b'S\xefB\xc8\xdf!^\xbeZ|z\xe8\x01\xcb\xc3\xac/\xacI)')

    wallet_1_addr = 'APRgMZHZubii29UXF9uFa6sohrsYupNAvx'

    import_watch_addr = UInt160(data=b'\xaf\x12\xa8h{\x14\x94\x8b\xc4\xa0\x08\x12\x8aU\nci[\xc1\xa5')
    watch_addr_str = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
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

        wallet = self.GetWallet1()

        self.assertEqual(len(wallet.LoadWatchOnly()), 0)

        result = ImportWatchAddr(wallet, self.watch_addr_str)

        self.assertEqual(len(wallet.LoadWatchOnly()), 1)

    def test_2_import_addr(self):

        wallet = self.GetWallet1()

        self.assertEqual(len(wallet.LoadWatchOnly()), 1)

        success = DeleteAddress(None, wallet, self.watch_addr_str)

        self.assertTrue(success)

        self.assertEqual(len(wallet.LoadWatchOnly()), 0)

    def test_3_import_token(self):

        wallet = self.GetWallet1()

        self.assertEqual(len(wallet.GetTokens()), 0)

        token_hash = 'f8d448b227991cf07cb96a6f9c0322437f1599b9'

        ImportToken(wallet, token_hash)

        token = list(wallet.GetTokens().values())[0]

        self.assertEqual(token.name, 'NEP5 Standard')
        self.assertEqual(token.symbol, 'NEP5')
        self.assertEqual(token.decimals, 8)
        self.assertEqual(token.Address, 'AYhE3Svuqdfh1RtzvE8hUhNR7HSpaSDFQg')

    def test_4_get_synced_balances(self):
        wallet = self.GetWallet1()
        synced_balances = wallet.GetSyncedBalances()
        self.assertEqual(len(synced_balances), 2)

    def test_5_show_unspent(self):

        wallet = self.GetWallet1(True)
        unspents = ShowUnspentCoins(wallet, [])
        self.assertEqual(len(unspents), 2)

        unspents = ShowUnspentCoins(wallet, ['neo'])
        self.assertEqual(len(unspents), 1)

        unspents = ShowUnspentCoins(wallet, ['gas'])
        self.assertEqual(len(unspents), 1)

        unspents = ShowUnspentCoins(wallet, ['APRgMZHZubii29UXF9uFa6sohrsYupNAvx'])
        self.assertEqual(len(unspents), 2)

        unspents = ShowUnspentCoins(wallet, ['AYhE3Svuqdfh1RtzvE8hUhNR7HSpaSDFQg'])
        self.assertEqual(len(unspents), 0)

        unspents = ShowUnspentCoins(wallet, ['--watch'])
        self.assertEqual(len(unspents), 0)

    def test_6_split_unspent(self):

        wallet = self.GetWallet1(True)

        # test bad
        tx = SplitUnspentCoin(wallet, [])
        self.assertEqual(tx, None)

        # bad inputs
        tx = SplitUnspentCoin(wallet, ['APRgMZHZubii29UXF9uFa6sohrsYupNAvx', 'neo', 3, 2])
        self.assertEqual(tx, None)

        # should be ok
        tx = SplitUnspentCoin(wallet, ['APRgMZHZubii29UXF9uFa6sohrsYupNAvx', 'neo', 0, 2], prompt_passwd=False)
        self.assertIsNotNone(tx)

        # rebuild wallet and try with non-even amount of neo, should be split into integer values of NEO
        wallet = self.GetWallet1(True)
        tx = SplitUnspentCoin(wallet, ['APRgMZHZubii29UXF9uFa6sohrsYupNAvx', 'neo', 0, 3], prompt_passwd=False)
        self.assertIsNotNone(tx)

        self.assertEqual([Fixed8.FromDecimal(34), Fixed8.FromDecimal(34), Fixed8.FromDecimal(32)], [item.Value for item in tx.outputs])

        # try with gas
        wallet = self.GetWallet1(True)
        tx = SplitUnspentCoin(wallet, ['APRgMZHZubii29UXF9uFa6sohrsYupNAvx', 'gas', 0, 3], prompt_passwd=False)
        self.assertIsNotNone(tx)
