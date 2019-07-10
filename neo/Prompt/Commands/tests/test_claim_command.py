from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Wallets.utils import to_aes_key
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Core.Blockchain import Blockchain
from neo.Core.UInt160 import UInt160
from neo.Prompt.Commands.Wallet import ClaimGas
from neo.Core.Fixed8 import Fixed8
from neo.Core.TX.ClaimTransaction import ClaimTransaction
from neo.Network.node import NeoNode
from neo.Network.nodemanager import NodeManager
import shutil
from mock import patch
from io import StringIO


class UserWalletTestCase(WalletFixtureTestCase):
    wallet_1_script_hash = UInt160(data=b'\x1c\xc9\xc0\\\xef\xff\xe6\xcd\xd7\xb1\x82\x81j\x91R\xec!\x8d.\xc0')

    wallet_1_addr = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'

    wallet_2_script_hash = UInt160(data=b'\x08t/\\P5\xac-\x0b\x1c\xb4\x94tIyBu\x7f1*')

    wallet_2_addr = 'AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEm'

    wallet_3_script_hash = UInt160(data=b'\xc4\xc1\xb0\xcf\xa8\x7f\xcb\xacE\x98W0\x16d\x11\x03]\xdf\xed#')

    wallet_3_addr = 'AZiE7xfyJALW7KmADWtCJXGGcnduYhGiCX'

    _wallet1 = None

    _wallet2 = None

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
    def GetWallet3(cls, recreate=False):
        if cls._wallet3 is None or recreate:
            shutil.copyfile(cls.wallet_3_path(), cls.wallet_3_dest())
            cls._wallet3 = UserWallet.Open(UserWalletTestCase.wallet_3_dest(),
                                           to_aes_key(UserWalletTestCase.wallet_3_pass()))
        return cls._wallet3

    def test_1_no_available_claim(self):

        wallet = self.GetWallet3()

        unspents = wallet.FindUnspentCoinsByAsset(self.NEO)

        self.assertEqual(1, len(unspents))

        unavailable_bonus = wallet.GetUnavailableBonus()

        self.assertEqual(Fixed8.FromDecimal(0.00028250).value, unavailable_bonus.value)

        unclaimed_coins = wallet.GetUnclaimedCoins()

        self.assertEqual(0, len(unclaimed_coins))

        available_bonus = wallet.GetAvailableClaimTotal()

        self.assertEqual(Fixed8.Zero(), available_bonus)

    def test_2_wallet_with_claimable_gas(self):

        wallet = self.GetWallet1()

        unspents = wallet.FindUnspentCoinsByAsset(self.NEO)

        self.assertEqual(1, len(unspents))

        unavailable_bonus = wallet.GetUnavailableBonus()

        self.assertEqual(Fixed8.FromDecimal(0.000629).value, unavailable_bonus.value)

        unclaimed_coins = wallet.GetUnclaimedCoins()

        self.assertEqual(1, len(unclaimed_coins))

        available_bonus = wallet.GetAvailableClaimTotal()

        self.assertEqual(Fixed8.FromDecimal(0.000288).value, available_bonus.value)

    def test_3_wallet_no_claimable_gas(self):

        wallet = self.GetWallet3()

        claim_tx, relayed = ClaimGas(wallet)

        self.assertFalse(relayed)

    def test_4_keyboard_interupt(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Wallet.prompt', side_effect=[KeyboardInterrupt]):
                wallet = self.GetWallet1()

                claim_tx, relayed = ClaimGas(wallet)
            self.assertEqual(claim_tx, None)
            self.assertFalse(relayed)
            self.assertIn("Claim transaction cancelled", mock_print.getvalue())

    def test_5_wallet_claim_ok(self):

        wallet = self.GetWallet1()
        nodemgr = NodeManager()
        nodemgr.nodes = [NeoNode(object, object)]

        with patch('neo.Network.node.NeoNode.relay', return_value=self.async_return(True)):
            with patch('neo.Prompt.Commands.Wallet.prompt', return_value=self.wallet_1_pass()):
                claim_tx, relayed = ClaimGas(wallet)
                self.assertIsInstance(claim_tx, ClaimTransaction)
                self.assertTrue(relayed)

    def test_6_no_wallet(self):
        with patch('neo.Prompt.Commands.Wallet.prompt', return_value=self.wallet_1_pass()):
            claim_tx, relayed = ClaimGas(None)
            self.assertEqual(claim_tx, None)
            self.assertFalse(relayed)

    def test_7_no_wallet(self):
        claim_tx, relayed = ClaimGas(None)
        self.assertEqual(claim_tx, None)
        self.assertFalse(relayed)

    def test_block_12248_sysfee(self):

        fee = Blockchain.Default().GetSysFeeAmountByHeight(12248)

        self.assertEqual(fee, 2050)

    def test_block_12323_sysfee(self):

        fee = Blockchain.Default().GetSysFeeAmountByHeight(12323)

        self.assertEqual(fee, 2540)

    def test_block_11351_sysfee(self):

        fee = Blockchain.Default().GetSysFeeAmountByHeight(11351)

        self.assertEqual(fee, 1560)
