from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Wallets.utils import to_aes_key
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Core.Blockchain import Blockchain
from neocore.UInt160 import UInt160
from neo.Prompt.Commands.Send import construct_and_send
from neo.Prompt.Commands.Wallet import ImportToken
from neo.Prompt.Utils import get_tx_attr_from_args
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

    def test_9_attributes(self):

        wallet = self.GetWallet1(recreate=True)

        args = ['gas', self.watch_addr_str, '2', "--tx-attr={'usage':241,'data':'This is a remark'}"]

        res = construct_and_send(None, wallet, args, prompt_password=False)

        self.assertTrue(res)

        self.assertEqual(2, len(res.Attributes))

    def test_10_attributes(self):
        wallet = self.GetWallet1(recreate=True)

        args = ['gas', self.watch_addr_str, '2', "--tx-attr=[{'usage':241,'data':'This is a remark'},{'usage':242,'data':'This is a remark 2'}]"]

        res = construct_and_send(None, wallet, args, prompt_password=False)

        self.assertTrue(res)

        self.assertEqual(3, len(res.Attributes))

    def test_11_bad_attributes(self):
        wallet = self.GetWallet1(recreate=True)

        args = ['gas', self.watch_addr_str, '2', "--tx-attr=[{'usa:241'data':his is a remark'}]"]

        res = construct_and_send(None, wallet, args, prompt_password=False)

        self.assertTrue(res)

        self.assertEqual(1, len(res.Attributes))

    def test_12_utils_attr_str(self):

        args = ["--tx-attr=[{'usa:241'data':his is a remark'}]"]

        with self.assertRaises(Exception) as context:
            args, txattrs = get_tx_attr_from_args(args)

            self.assertTrue('could not convert object' in context.exception)
            self.assertEqual(len(args), 0)
            self.assertEqual(len(txattrs), 0)

    def test_13_utilst_bad_type(self):

        args = ["--tx-attr=bytearray(b'\x00\x00')"]

        with self.assertRaises(Exception) as context:

            args, txattr = get_tx_attr_from_args(args)
            self.assertTrue('could not convert object' in context.exception)
            self.assertEqual(len(args), 0)
            self.assertEqual(len(txattr), 0)
