from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Wallets.utils import to_aes_key
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB
from neo.Core.Blockchain import Blockchain
from neocore.UInt160 import UInt160
from neo.Prompt.Commands.Wallet import ImportToken
from neo.Prompt.Commands.Tokens import token_get_allowance, \
    token_approve_allowance, token_send, token_send_from, token_history, token_mint
import shutil
from neocore.IO.BinaryWriter import BinaryWriter
from neo.IO.MemoryStream import StreamManager


class UserWalletTestCase(WalletFixtureTestCase):

    wallet_1_script_hash = UInt160(data=b'S\xefB\xc8\xdf!^\xbeZ|z\xe8\x01\xcb\xc3\xac/\xacI)')

    wallet_1_addr = 'APRgMZHZubii29UXF9uFa6sohrsYupNAvx'

    import_watch_addr = UInt160(data=b'\xaf\x12\xa8h{\x14\x94\x8b\xc4\xa0\x08\x12\x8aU\nci[\xc1\xa5')
    watch_addr_str = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
    _wallet1 = None

    token_hash_str = 'f8d448b227991cf07cb96a6f9c0322437f1599b9'

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

    def get_token(self, wallet):
        try:
            return list(wallet.GetTokens().values())[0]
        except Exception as e:
            pass
        return None

    def test_1_import_token(self):

        wallet = self.GetWallet1()

        self.assertEqual(len(wallet.GetTokens()), 0)

        ImportToken(wallet, self.token_hash_str)

        token = list(wallet.GetTokens().values())[0]

        self.assertEqual(token.name, 'NEP5 Standard')
        self.assertEqual(token.symbol, 'NEP5')
        self.assertEqual(token.decimals, 8)
        self.assertEqual(token.Address, 'AYhE3Svuqdfh1RtzvE8hUhNR7HSpaSDFQg')

    def test_2_token_balance(self):

        wallet = self.GetWallet1()

        token = self.get_token(wallet)

        balance = wallet.GetBalance(token)

        self.assertEqual(balance, 9999)

    def test_3_token_allowance(self):

        wallet = self.GetWallet1()

        token = self.get_token(wallet)

        addr_to = wallet.GetDefaultContract().Address

        args = [token.symbol, self.watch_addr_str, addr_to]

        allowance = token_get_allowance(wallet, args, verbose=False)

        self.assertEqual(allowance, 0)

    def test_4_token_send(self):

        wallet = self.GetWallet1(recreate=True)

        ImportToken(wallet, self.token_hash_str)

        token = self.get_token(wallet)

        addr_from = wallet.GetDefaultContract().Address

        addr_to = self.watch_addr_str

        args = [token.symbol, addr_from, addr_to, '1300']

        # this should fail, since it is more than current balance
        send = token_send(wallet, args, prompt_passwd=False)

        self.assertTrue(send)

    def test_5_token_approve(self):

        # we need to reset the wallet now
        wallet = self.GetWallet1(recreate=True)

        ImportToken(wallet, self.token_hash_str)

        token = self.get_token(wallet)

        addr_from = wallet.GetDefaultContract().Address

        addr_to = self.watch_addr_str

        args = [token.symbol, addr_from, addr_to, '123']

        send = token_approve_allowance(wallet, args, prompt_passwd=False)

        self.assertTrue(send)

    def test_6_transfer_from(self):

        # we need to reset the wallet now
        wallet = self.GetWallet1(recreate=True)

        ImportToken(wallet, self.token_hash_str)

        token = self.get_token(wallet)

        addr_from = wallet.GetDefaultContract().Address

        addr_to = self.watch_addr_str

        args = [token.symbol, addr_from, addr_to, '123']

        # this should be false, since this wallet has no allowance
        send = token_send_from(wallet, args, prompt_passwd=False)

        self.assertFalse(send)

    def test_7_token_history_correct(self):

        wallet = self.GetWallet1(recreate=True)

        ImportToken(wallet, self.token_hash_str)

        db = NotificationDB.instance()

        token = self.get_token(wallet)

        result = token_history(wallet, db, [token.symbol])

        self.assertTrue(result)

        db.close()

    def test_7_token_history_no_token(self):

        wallet = self.GetWallet1(recreate=True)

        ImportToken(wallet, self.token_hash_str)

        db = NotificationDB.instance()

        result = token_history(wallet, db, ["BAD"])

        self.assertFalse(result)

        db.close()

    def test_7_token_history_no_args(self):

        wallet = self.GetWallet1(recreate=True)

        ImportToken(wallet, self.token_hash_str)

        result = token_history(wallet, None, [])

        self.assertFalse(result)

    def test_7_token_history_no_db(self):

        wallet = self.GetWallet1(recreate=True)

        ImportToken(wallet, self.token_hash_str)

        result = token_history(wallet, None, ['abc'])

        self.assertFalse(result)

    # this will fail since this token doesn't have a mint method
    def test_8_mint(self):

        wallet = self.GetWallet1(recreate=True)

        ImportToken(wallet, self.token_hash_str)

        token = self.get_token(wallet)

        addr_to = self.wallet_1_addr

        args = [token.symbol, addr_to, '--attach-neo=10']

        mint = token_mint(wallet, args, prompt_passwd=False)

        self.assertFalse(mint)

    def test_token_serialize(self):

        wallet = self.GetWallet1(recreate=True)

        ImportToken(wallet, self.token_hash_str)

        token = self.get_token(wallet)

        stream = StreamManager.GetStream()
        writer = BinaryWriter(stream)
        token.Serialize(writer)

        self.assertEqual(b'0d4e455035205374616e64617264044e45503508', stream.ToArray())
