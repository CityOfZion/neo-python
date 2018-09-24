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

    wallet_1_script_hash = UInt160(data=b'\x1c\xc9\xc0\\\xef\xff\xe6\xcd\xd7\xb1\x82\x81j\x91R\xec!\x8d.\xc0')

    wallet_1_addr = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'

    import_watch_addr = UInt160(data=b'\x08t/\\P5\xac-\x0b\x1c\xb4\x94tIyBu\x7f1*')
    watch_addr_str = 'AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEm'
    _wallet1 = None

    token_hash_str = '31730cc9a1844891a3bafd1aa929a4142860d8d3'

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

        self.assertEqual(len(wallet.GetTokens()), 1)

        ImportToken(wallet, self.token_hash_str)

        token = list(wallet.GetTokens().values())[0]

        self.assertEqual(token.name, 'NEX Template V4')
        self.assertEqual(token.symbol, 'NXT4')
        self.assertEqual(token.decimals, 8)
        self.assertEqual(token.Address, 'Ab61S1rk2VtCVd3NtGNphmBckWk4cfBdmB')

    def test_2_token_balance(self):

        wallet = self.GetWallet1()

        token = self.get_token(wallet)

        balance = wallet.GetBalance(token)

        self.assertEqual(balance, 2499000)

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

    def test_8_mint(self):

        wallet = self.GetWallet1(recreate=True)

        ImportToken(wallet, self.token_hash_str)

        token = self.get_token(wallet)

        addr_to = self.wallet_1_addr

        args = [token.symbol, addr_to, '--attach-neo=10']

        mint = token_mint(wallet, args, prompt_passwd=False)

        self.assertTrue(mint)

    def test_token_serialize(self):

        wallet = self.GetWallet1(recreate=True)

        ImportToken(wallet, self.token_hash_str)

        token = self.get_token(wallet)

        stream = StreamManager.GetStream()
        writer = BinaryWriter(stream)
        token.Serialize(writer)

        self.assertEqual(b'0f4e45582054656d706c617465205634044e58543408', stream.ToArray())
