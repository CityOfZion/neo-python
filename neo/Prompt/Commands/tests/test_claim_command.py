from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Core.Blockchain import Blockchain
from neocore.UInt160 import UInt160
from neo.Prompt.Commands.Wallet import ClaimGas
from neocore.Fixed8 import Fixed8
import shutil
import pdb


class UserWalletTestCase(WalletFixtureTestCase):

    wallet_1_script_hash = UInt160(data=b'S\xefB\xc8\xdf!^\xbeZ|z\xe8\x01\xcb\xc3\xac/\xacI)')

    wallet_1_addr = 'APRgMZHZubii29UXF9uFa6sohrsYupNAvx'

    wallet_3_script_hash = UInt160(data=b'\xa6\xc5\x9d\xeb\xf0\xd7(\xbd\x14\x89\xcd\xb9\xd9{\xd1\x90\xcb\x0b\xdch')

    wallet_3_addr = 'AWygZ1B5c3GDiLL6u5bHSVU45Ya1SVGX9P'

    _wallet1 = None

    _wallet3 = None

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
            cls._wallet1 = UserWallet.Open(UserWalletTestCase.wallet_1_dest(), UserWalletTestCase.wallet_1_pass())
        return cls._wallet1

    @classmethod
    def GetWallet3(cls, recreate=False):
        if cls._wallet3 is None or recreate:
            shutil.copyfile(cls.wallet_3_path(), cls.wallet_3_dest())
            cls._wallet3 = UserWallet.Open(UserWalletTestCase.wallet_3_dest(), UserWalletTestCase.wallet_3_pass())
        return cls._wallet3

    def test_1_no_available_claim(self):

        wallet = self.GetWallet1()

        unspents = wallet.FindUnspentCoinsByAsset(self.NEO)

        self.assertEqual(1, len(unspents))

        unavailable_bonus = wallet.GetUnavailableBonus()

        self.assertEqual(Fixed8.FromDecimal(0.124316), unavailable_bonus)

        unclaimed_coins = wallet.GetUnclaimedCoins()

        self.assertEqual(0, len(unclaimed_coins))

        available_bonus = wallet.GetAvailableClaimTotal()

        self.assertEqual(Fixed8.Zero(), available_bonus)

    def test_2_wallet_with_claimable_gas(self):

        wallet = self.GetWallet3()

        unspents = wallet.FindUnspentCoinsByAsset(self.NEO)

        self.assertEqual(2, len(unspents))

        unavailable_bonus = wallet.GetUnavailableBonus()

        self.assertEqual(Fixed8.FromDecimal(0.00036456), unavailable_bonus)

        unclaimed_coins = wallet.GetUnclaimedCoins()

        self.assertEqual(4, len(unclaimed_coins))

        available_bonus = wallet.GetAvailableClaimTotal()

        self.assertEqual(Fixed8.FromDecimal(0.0048411), available_bonus)

    def test_3_wallet_no_claimable_gas(self):

        wallet = self.GetWallet1()

        result = ClaimGas(wallet, require_password=False)

        self.assertFalse(result)

    def test_4_wallet_claim_ok(self):

        wallet = self.GetWallet3()

        claim = ClaimGas(wallet, require_password=False)

        self.assertTrue(claim)

    def test_block_150000_sysfee(self):

        fee = Blockchain.Default().GetSysFeeAmountByHeight(150000)

        self.assertEqual(fee, 1230)

    def test_block_347809_sysfee(self):

        fee = Blockchain.Default().GetSysFeeAmountByHeight(347809)

        self.assertEqual(fee, 39134)

    def test_block_747809_sysfee(self):

        fee = Blockchain.Default().GetSysFeeAmountByHeight(747809)

        self.assertEqual(fee, 472954)
