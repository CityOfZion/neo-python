from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Wallets.utils import to_aes_key
from neo.Core.Blockchain import Blockchain
from neocore.UInt160 import UInt160
from neocore.KeyPair import KeyPair


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
            cls._wallet1 = UserWallet.Create(UserWalletTestCase.new_wallet_dest(),
                                             to_aes_key('awesomepassword'))
        return cls._wallet1

    def test_1_initial_setup(self):

        wallet = self.GetWallet1()

        jsn = wallet.ToJson()

        addr = jsn['addresses'][0]

        self.assertEqual(len(jsn['addresses']), 1)

    def test_3_import_wif(self):

        wallet = self.GetWallet1()

        key_to_import = 'L3MBUkKU5kYg16KSZnqcaTj2pG5ei3fN9A4X7rxXys18GBDa3bH8'

        prikey = KeyPair.PrivateKeyFromWIF(key_to_import)
        keypair = wallet.CreateKey(prikey)

        key_out = keypair.PublicKey.encode_point(True).decode('utf-8')

        self.assertEqual(key_out, '03f3a3b5a4d873933fc7f4b53113e8eb999fb20038271fbbb10255585670c3c312')

        self.assertEqual(len(wallet.GetContracts()), 2)

    def test_4_delete_addr(self):

        wallet = self.GetWallet1()

        self.assertEqual(len(wallet.GetContracts()), 2)

        imported_addr = UInt160(data=b'\xec\xa8\xfc\xf9Nz*\x7f\xc3\xfdT\xae\x0e\xd3\xd3MR\xec%\x90')

        wallet.DeleteAddress(imported_addr)

        self.assertEqual(len(wallet.GetContracts()), 1)

    def test_5_addr_conv(self):

        wallet = self.GetWallet1()
        addr = UInt160(data=b'\xec\xa8\xfc\xf9Nz*\x7f\xc3\xfdT\xae\x0e\xd3\xd3MR\xec%\x90')

        addr_str = 'AdMDZGto3xWozB1HSjjVv27RL3zUM8LzpV'

        to_uint = wallet.ToScriptHash(addr_str)

        self.assertEqual(to_uint, addr)

    def test_6_standard_addr(self):

        wallet = self.GetWallet1()

        addr = wallet.GetStandardAddress()

        self.assertIsInstance(addr, UInt160)

        default = wallet.GetDefaultContract()

        self.assertEqual(default.ScriptHash, addr)

    def test_7_change_password(self):

        wallet = self.GetWallet1()

        wallet.ChangePassword('awesomepassword', 'awesomepassword2')

        self.assertIsNotNone(wallet)

    def test_8_create_bad_path(self):

        self.assertRaises(Exception, UserWallet.Create, './path/to/nonexistent/wallet.db3', 'blah')
