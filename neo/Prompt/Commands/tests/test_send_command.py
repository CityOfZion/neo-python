from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Core.Blockchain import Blockchain
from neocore.UInt160 import UInt160
from neo.Prompt.Commands.Send import construct_and_send
from neo.Prompt.Commands.Wallet import ImportToken
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
            cls._wallet1 = UserWallet.Open(UserWalletTestCase.wallet_1_dest(), UserWalletTestCase.wallet_1_pass())
        return cls._wallet1

    def test_1_send_neo(self):

        wallet = self.GetWallet1(recreate=True)

        args = ['neo', self.watch_addr_str, '50']

        res = construct_and_send(None, wallet, args, prompt_password=False)

        self.assertTrue(res)

    def test_2_send_gas(self):

        wallet = self.GetWallet1(recreate=True)

        args = ['gas', self.watch_addr_str, '50']

        res = construct_and_send(None, wallet, args, prompt_password=False)

        self.assertTrue(res)

    def test_3_insufficient_funds(self):

        wallet = self.GetWallet1(recreate=True)

        args = ['gas', self.watch_addr_str, '101']

        res = construct_and_send(None, wallet, args, prompt_password=False)

        self.assertFalse(res)

    def test_4_bad_assetid(self):

        wallet = self.GetWallet1(recreate=True)

        args = ['blah', self.watch_addr_str, '12']

        res = construct_and_send(None, wallet, args, prompt_password=False)

        self.assertFalse(res)

    def test_5_negative(self):

        wallet = self.GetWallet1(recreate=True)

        args = ['neo', self.watch_addr_str, '-12']

        res = construct_and_send(None, wallet, args, prompt_password=False)

        self.assertFalse(res)

    def test_6_weird_amount(self):

        wallet = self.GetWallet1(recreate=True)

        args = ['neo', self.watch_addr_str, '12.abc3']

        res = construct_and_send(None, wallet, args, prompt_password=False)

        self.assertFalse(res)

    def test_7_send_token_bad(self):

        wallet = self.GetWallet1(recreate=True)

        token_hash = 'f8d448b227991cf07cb96a6f9c0322437f1599b9'

        ImportToken(wallet, token_hash)

        args = ['NEP5', self.watch_addr_str, '32']

        res = construct_and_send(None, wallet, args, prompt_password=False)

        self.assertFalse(res)

    def test_8_send_token_ok(self):

        wallet = self.GetWallet1(recreate=True)

        token_hash = 'f8d448b227991cf07cb96a6f9c0322437f1599b9'

        ImportToken(wallet, token_hash)

        args = ['NEP5', self.watch_addr_str, '32', '--from-addr=%s' % self.wallet_1_addr]

        res = construct_and_send(None, wallet, args, prompt_password=False)

        self.assertTrue(res)
