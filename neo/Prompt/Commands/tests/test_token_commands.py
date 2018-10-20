from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Wallets.utils import to_aes_key
from neo.Prompt.Utils import get_asset_id
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB
from neo.Core.Blockchain import Blockchain
from neocore.UInt160 import UInt160
from neo.Prompt.Commands.Wallet import ImportToken
from neo.Prompt.Commands.Tokens import token_get_allowance, token_approve_allowance, \
    token_send, token_send_from, token_history, token_mint, token_crowdsale_register, amount_from_string
import shutil
from neocore.IO.BinaryWriter import BinaryWriter
from neo.IO.MemoryStream import StreamManager
from mock import patch
import json


class UserWalletTestCase(WalletFixtureTestCase):

    wallet_1_addr = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'

    watch_addr_str = 'AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEm'

    _wallet1 = None

    wallet_2_addr = 'AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEm'

    _wallet2 = None

    wallet_3_addr = 'AZiE7xfyJALW7KmADWtCJXGGcnduYhGiCX'

    _wallet3 = None

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

    def get_tokens(self, wallet):
        return list(wallet.GetTokens().values())[0]

    def test_import_token(self):
        wallet = self.GetWallet3(recreate=True)

        self.assertEqual(len(wallet.GetTokens()), 0)

        ImportToken(wallet, self.token_hash_str)

        token = list(wallet.GetTokens().values())[0]

        self.assertEqual(token.name, 'NEX Template V4')
        self.assertEqual(token.symbol, 'NXT4')
        self.assertEqual(token.decimals, 8)
        self.assertEqual(token.Address, 'Ab61S1rk2VtCVd3NtGNphmBckWk4cfBdmB')

    def test_token_balance(self):
        wallet = self.GetWallet1(recreate=True)

        token = self.get_tokens(wallet)

        balance = wallet.GetBalance(token)

        self.assertEqual(balance, 2499000)

    def test_token_send_good(self):
        with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_tokens(wallet)
            addr_from = wallet.GetDefaultContract().Address
            addr_to = self.watch_addr_str

            args = [token.symbol, addr_from, addr_to, '1300']
            send = token_send(wallet, args, prompt_passwd=True)

            self.assertTrue(send)
            res = send.ToJson()
            self.assertEqual(res["vout"][0]["address"], "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3")
            self.assertEqual(res["net_fee"], "0.0001")

    def test_token_send_bad_args(self):  # too few args
        wallet = self.GetWallet1(recreate=True)
        token = self.get_tokens(wallet)
        addr_from = wallet.GetDefaultContract().Address
        addr_to = self.watch_addr_str

        args = [token.symbol, addr_from, addr_to]
        send = token_send(wallet, args, prompt_passwd=False)

        self.assertFalse(send)

    def test_token_send_no_tx(self):
        with patch('neo.Wallets.NEP5Token.NEP5Token.Transfer', return_value=(None, 0, None)):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_tokens(wallet)
            addr_from = wallet.GetDefaultContract().Address
            addr_to = self.watch_addr_str

            args = [token.symbol, addr_from, addr_to, '1300']
            send = token_send(wallet, args, prompt_passwd=False)

            self.assertFalse(send)

    def test_token_send_bad_password(self):
        with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=["blah"]):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_tokens(wallet)
            addr_from = wallet.GetDefaultContract().Address
            addr_to = self.watch_addr_str

            args = [token.symbol, addr_from, addr_to, '1300']
            send = token_send(wallet, args)

            self.assertFalse(send)

    def test_transfer_from_good(self):
        with patch('neo.Prompt.Commands.Tokens.token_get_allowance', return_value=12300000000):
            with patch('neo.Wallets.NEP5Token.NEP5Token.TransferFrom', return_value=(self.Approve_Allowance())):
                with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
                    wallet = self.GetWallet1(recreate=True)
                    token = self.get_tokens(wallet)
                    addr_from = self.wallet_1_addr
                    addr_to = self.watch_addr_str

                    args = [token.symbol, addr_from, addr_to, '123']
                    send = token_send_from(wallet, args, prompt_passwd=True)

                    # expected to be false because TransferFrom patch returns a tx which cannot be relayed
                    self.assertFalse(send)

    def test_transfer_from_bad_args(self):  # too few args
        wallet = self.GetWallet1(recreate=True)
        token = self.get_tokens(wallet)
        addr_from = self.wallet_1_addr
        addr_to = self.watch_addr_str

        args = [token.symbol, addr_from, addr_to]
        send = token_send_from(wallet, args, prompt_passwd=False)

        self.assertFalse(send)

    def test_transfer_from_small_allowance(self):
        wallet = self.GetWallet1(recreate=True)
        token = self.get_tokens(wallet)
        addr_from = self.wallet_1_addr
        addr_to = self.watch_addr_str

        args = [token.symbol, addr_from, addr_to, '123']
        send = token_send_from(wallet, args, prompt_passwd=False)

        # expected to be false because there are no approved allowances
        self.assertFalse(send)

    def test_transfer_from_BigInteger_0(self):
        with patch('neo.Prompt.Commands.Tokens.token_get_allowance', return_value=12300000000):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_tokens(wallet)
            addr_from = self.wallet_1_addr
            addr_to = self.watch_addr_str

            args = [token.symbol, addr_from, addr_to, '123']
            send = token_send_from(wallet, args, prompt_passwd=False)

            # expected to be false because results[0].GetBigInteger() == 0
            self.assertFalse(send)

    def test_transfer_from_bad_password(self):
        with patch('neo.Prompt.Commands.Tokens.token_get_allowance', return_value=12300000000):
            with patch('neo.Wallets.NEP5Token.NEP5Token.TransferFrom', return_value=(self.Approve_Allowance())):
                with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=['blah']):
                    wallet = self.GetWallet1(recreate=True)
                    token = self.get_tokens(wallet)
                    addr_from = self.wallet_1_addr
                    addr_to = self.watch_addr_str

                    args = [token.symbol, addr_from, addr_to, '123']
                    send = token_send_from(wallet, args, prompt_passwd=True)

                    self.assertFalse(send)

    def test_token_approve_good(self):
        with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_tokens(wallet)
            addr_from = wallet.GetDefaultContract().Address
            addr_to = self.watch_addr_str

            args = [token.symbol, addr_from, addr_to, '123']
            send = token_approve_allowance(wallet, args, prompt_passwd=True)

            self.assertTrue(send)
            res = send.ToJson()
            self.assertEqual(res["vout"][0]["address"], "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3")
            self.assertEqual(res["net_fee"], "0.0001")

    def test_token_approve_bad_args(self):  # too few args
        wallet = self.GetWallet1(recreate=True)
        token = self.get_tokens(wallet)
        addr_from = wallet.GetDefaultContract().Address
        addr_to = self.watch_addr_str

        args = [token.symbol, addr_from, addr_to]
        send = token_approve_allowance(wallet, args, prompt_passwd=False)

        self.assertFalse(send)

    def test_token_approve_no_tx(self):
        with patch('neo.Wallets.NEP5Token.NEP5Token.Approve', return_value=(None, 0, None)):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_tokens(wallet)
            addr_from = wallet.GetDefaultContract().Address
            addr_to = self.watch_addr_str

            args = [token.symbol, addr_from, addr_to, '123']
            send = token_approve_allowance(wallet, args, prompt_passwd=False)

            self.assertFalse(send)

    def test_token_approve_bad_password(self):
        with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=["blah"]):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_tokens(wallet)
            addr_from = wallet.GetDefaultContract().Address
            addr_to = self.watch_addr_str

            args = [token.symbol, addr_from, addr_to, '123']
            send = token_approve_allowance(wallet, args, prompt_passwd=True)

            self.assertFalse(send)

    def test_token_allowance_good(self):
        with patch('neo.Wallets.NEP5Token.NEP5Token.Allowance', return_value=(self.Approve_Allowance())):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_tokens(wallet)
            addr_to = self.watch_addr_str

            args = [token.symbol, self.wallet_1_addr, addr_to]
            allowance = token_get_allowance(wallet, args, verbose=True)

            self.assertTrue(allowance)

    def test_token_allowance_bad_args(self):  # too few args
        wallet = self.GetWallet1(recreate=True)
        token = self.get_tokens(wallet)

        args = [token.symbol, self.wallet_1_addr]
        allowance = token_get_allowance(wallet, args, verbose=True)

        self.assertFalse(allowance)

    def test_token_allowance_no_tx(self):
        with patch('neo.Wallets.NEP5Token.NEP5Token.Allowance', return_value=(None, 0, None)):

            wallet = self.GetWallet1(recreate=True)
            token = self.get_tokens(wallet)
            addr_to = self.watch_addr_str

            args = [token.symbol, self.wallet_1_addr, addr_to]
            allowance = token_get_allowance(wallet, args, verbose=True)

            self.assertEqual(allowance, 0)

    def test_token_mint_good(self):
        with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_tokens(wallet)
            addr_to = self.wallet_1_addr

            args = [token.symbol, addr_to, '--attach-neo=10', '--tx-attr={"usage":241,"data":"This is a remark"}']
            mint = token_mint(wallet, args, prompt_passwd=True)

            self.assertTrue(mint)
            res = mint.ToJson()
            self.assertEqual(res['attributes'][1]['usage'], 241)  # verifies attached attribute
            self.assertEqual(res['vout'][0]['value'], "10")  # verifies attached neo
            self.assertEqual(res['vout'][0]['address'], "Ab61S1rk2VtCVd3NtGNphmBckWk4cfBdmB")  # verifies attached neo sent to token contract owner

    def test_token_mint_bad_args(self):  # too few args
        wallet = self.GetWallet1(recreate=True)
        token = self.get_tokens(wallet)
        addr_to = self.wallet_1_addr

        args = [token.symbol, addr_to]
        mint = token_mint(wallet, args, prompt_passwd=False)

        self.assertFalse(mint)

    def test_token_mint_no_tx(self):
        with patch('neo.Wallets.NEP5Token.NEP5Token.Mint', return_value=(None, 0, None)):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_tokens(wallet)
            addr_to = self.wallet_1_addr

            args = [token.symbol, addr_to, '--attach-neo=10']
            mint = token_mint(wallet, args, prompt_passwd=False)

            self.assertFalse(mint)

    def test_token_mint_bad_password(self):
        with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=["blah"]):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_tokens(wallet)
            addr_to = self.wallet_1_addr

            args = [token.symbol, addr_to, '--attach-neo=10']
            mint = token_mint(wallet, args, prompt_passwd=True)

            self.assertFalse(mint)

    def test_token_register_good(self):
        with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_tokens(wallet)

            args = [token.symbol, self.wallet_3_addr, self.watch_addr_str, "--from-addr=AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3"]
            register = token_crowdsale_register(wallet, args, prompt_passwd=True)

            self.assertTrue(register)
            res = register.ToJson()
            self.assertEqual(res['vout'][0]['address'], "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3")
            self.assertEqual(res['net_fee'], "0.0001")

    def test_token_register_bad_args(self):  # too few args
        wallet = self.GetWallet1(recreate=True)
        token = self.get_tokens(wallet)

        args = [token.symbol]
        register = token_crowdsale_register(wallet, args, prompt_passwd=False)

        self.assertFalse(register)

    def test_token_register_no_tx(self):
        with patch('neo.Wallets.NEP5Token.NEP5Token.CrowdsaleRegister', return_value=(None, 0, None)):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_tokens(wallet)

            args = [token.symbol, self.wallet_3_addr]
            register = token_crowdsale_register(wallet, args, prompt_passwd=False)

            self.assertFalse(register)

    def test_token_register_bad_password(self):
        with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=["blah"]):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_tokens(wallet)

            args = [token.symbol, self.wallet_3_addr]
            register = token_crowdsale_register(wallet, args, prompt_passwd=True)

            self.assertFalse(register)

    def test_token_history_correct(self):
        db = NotificationDB.instance()

        # test Send event history
        wallet = self.GetWallet1(recreate=True)

        result = token_history(wallet, db, ["NXT4"])
        self.assertTrue(result)

        # test Received event history
        wallet = self.GetWallet2(recreate=True)

        result = token_history(wallet, db, ["NXT4"])
        self.assertTrue(result)

        db.close()

    def test_token_history_no_args(self):
        wallet = self.GetWallet1(recreate=True)
        db = NotificationDB.instance()

        result = token_history(wallet, db, [])

        self.assertFalse(result)

        db.close()

    def test_token_history_no_db(self):
        wallet = self.GetWallet1(recreate=True)

        result = token_history(wallet, None, ["NXT4"])

        self.assertFalse(result)

    def test_token_history_no_token(self):
        wallet = self.GetWallet1(recreate=True)
        db = NotificationDB.instance()

        result = token_history(wallet, db, ["BAD"])

        self.assertFalse(result)

        db.close()

    def test_token_serialize(self):

        wallet = self.GetWallet1(recreate=True)
        token = self.get_tokens(wallet)

        stream = StreamManager.GetStream()
        writer = BinaryWriter(stream)
        token.Serialize(writer)

        self.assertEqual(b'0f4e45582054656d706c617465205634044e58543408', stream.ToArray())

    # utility function
    def Approve_Allowance(self):
        wallet = self.GetWallet1(recreate=True)
        approve_from = self.wallet_1_addr
        approve_to = self.watch_addr_str
        tokens = self.get_tokens(wallet)
        token = get_asset_id(wallet, tokens.symbol)
        amount = amount_from_string(token, "123")

        tx, fee, results = token.Approve(wallet, approve_from, approve_to, amount)

        return tx, fee, results
