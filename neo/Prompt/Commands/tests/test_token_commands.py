import os
from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Wallets.utils import to_aes_key
from neo.Prompt.Utils import get_asset_id, get_tx_attr_from_args
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Core.Blockchain import Blockchain
from neo.Prompt.Commands.Wallet import CommandWallet
from neo.Prompt.Commands.WalletImport import ImportToken
from neo.Prompt.Commands.Tokens import token_get_allowance, token_send, token_history, token_mint, amount_from_string
from neo.Prompt import Utils as PromptUtils
import shutil
from neocore.IO.BinaryWriter import BinaryWriter
from neocore.Fixed8 import Fixed8
from neo.IO.MemoryStream import StreamManager
from mock import patch
from neo.Prompt.PromptData import PromptData
from contextlib import contextmanager
from io import StringIO, TextIOWrapper
from neo.VM.InteropService import StackItem
from neo.Prompt.PromptPrinter import pp


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

    @contextmanager
    def OpenWallet1(self):
        PromptData.Wallet = UserWalletTestCase.GetWallet1(recreate=True)

        yield

        filename = UserWalletTestCase.wallet_1_dest()
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except OSError:
                pass
        PromptData.Wallet = None

    @contextmanager
    def OpenWallet2(self):
        PromptData.Wallet = UserWalletTestCase.GetWallet2(recreate=True)

        yield

        filename = UserWalletTestCase.wallet_2_dest()
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except OSError:
                pass
        PromptData.Wallet = None

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

        token = self.get_token(wallet)

        balance = wallet.GetBalance(token)

        self.assertEqual(balance, 2499000)

    def test_token_send_good(self):
        with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_token(wallet)
            addr_from = wallet.GetDefaultContract().Address
            addr_to = self.watch_addr_str
            fee = Fixed8.FromDecimal(0.001)

            send = token_send(wallet, token.symbol, addr_from, addr_to, 1300, fee)

            self.assertTrue(send)
            res = send.ToJson()
            self.assertEqual(res["vout"][0]["address"], "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3")
            self.assertEqual(res["net_fee"], "0.0011")

    def test_token_send_with_user_attributes(self):
        with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_token(wallet)
            addr_from = wallet.GetDefaultContract().Address
            addr_to = self.watch_addr_str
            _, attributes = get_tx_attr_from_args(['--tx-attr=[{"usage":241,"data":"This is a remark"},{"usage":242,"data":"This is a remark 2"}]'])

            send = token_send(wallet, token.symbol, addr_from, addr_to, 1300, user_tx_attributes=attributes)

            self.assertTrue(send)
            res = send.ToJson()
            self.assertEqual(len(res['attributes']), 3)
            self.assertEqual(res['attributes'][0]['usage'], 241)
            self.assertEqual(res['attributes'][1]['usage'], 242)

    def test_token_send_bad_user_attributes(self):
        with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_token(wallet)
            addr_from = wallet.GetDefaultContract().Address
            addr_to = self.watch_addr_str

            _, attributes = get_tx_attr_from_args(['--tx-attr=[{"usa:241,"data":"This is a remark"}]'])
            send = token_send(wallet, token.symbol, addr_from, addr_to, 100, user_tx_attributes=attributes)

            self.assertTrue(send)
            res = send.ToJson()
            self.assertEqual(1, len(res['attributes']))
            self.assertNotEqual(241, res['attributes'][0]['usage'])

    def test_token_send_bad_args(self):  # too few args
        wallet = self.GetWallet1(recreate=True)
        token = self.get_token(wallet)
        addr_from = wallet.GetDefaultContract().Address
        addr_to = self.watch_addr_str

        with self.assertRaises(ValueError) as context:
            token_send(wallet, token.symbol, addr_from, addr_to, None)

        self.assertIn("not a valid amount", str(context.exception))

    def test_token_send_bad_token(self):
        wallet = self.GetWallet1(recreate=True)
        addr_from = wallet.GetDefaultContract().Address
        addr_to = self.watch_addr_str

        with self.assertRaises(ValueError) as context:
            token_send(wallet, "Blah", addr_from, addr_to, 1300)

        self.assertIn("does not represent a known NEP5 token", str(context.exception))

    def test_token_send_no_tx(self):
        with patch('neo.Wallets.NEP5Token.NEP5Token.Transfer', return_value=(None, 0, None)):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_token(wallet)
            addr_from = wallet.GetDefaultContract().Address
            addr_to = self.watch_addr_str

            send = token_send(wallet, token.symbol, addr_from, addr_to, 1300)

            self.assertFalse(send)

    def test_token_send_bad_password(self):
        with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=["blah"]):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_token(wallet)
            addr_from = wallet.GetDefaultContract().Address
            addr_to = self.watch_addr_str

            send = token_send(wallet, token.symbol, addr_from, addr_to, 1300)

            self.assertFalse(send)

    def test_token_allowance_good(self):
        with patch('neo.Wallets.NEP5Token.NEP5Token.Allowance', return_value=(self.Approve_Allowance())):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_token(wallet)
            addr_to = self.watch_addr_str

            allowance = token_get_allowance(wallet, token.symbol, self.wallet_1_addr, addr_to, verbose=True)

            self.assertTrue(allowance)

    def test_token_allowance_bad_token(self):
        wallet = self.GetWallet1(recreate=True)
        addr_to = self.watch_addr_str

        with self.assertRaises(ValueError) as context:
            token_get_allowance(wallet, "bad_token", self.wallet_1_addr, addr_to, verbose=True)

        self.assertIn("not represent a known NEP5", str(context.exception))

    def test_token_allowance_no_tx(self):
        with patch('neo.Wallets.NEP5Token.NEP5Token.Allowance', return_value=(None, 0, None)):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_token(wallet)
            addr_to = self.watch_addr_str

            with self.assertRaises(ValueError) as context:
                token_get_allowance(wallet, token.symbol, self.wallet_1_addr, addr_to, verbose=True)

            self.assertIn("Could not get allowance", str(context.exception))

    def test_token_mint_good(self):
        with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_token(wallet)
            addr_to = self.wallet_1_addr
            asset_attachments = ['--attach-neo=10']
            _, tx_attr = PromptUtils.get_tx_attr_from_args(['--tx-attr={"usage":241,"data":"This is a remark"}'])

            mint = token_mint(token, wallet, addr_to, asset_attachments=asset_attachments, invoke_attrs=tx_attr)

            self.assertTrue(mint)
            res = mint.ToJson()
            self.assertEqual(res['attributes'][1]['usage'], 241)  # verifies attached attribute
            self.assertEqual(res['vout'][0]['value'], "10")  # verifies attached neo
            self.assertEqual(res['vout'][0]['address'], "Ab61S1rk2VtCVd3NtGNphmBckWk4cfBdmB")  # verifies attached neo sent to token contract owner

    def test_token_mint_no_tx(self):
        with patch('neo.Wallets.NEP5Token.NEP5Token.Mint', return_value=(None, 0, None)):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_token(wallet)
            addr_to = self.wallet_1_addr
            asset_attachments = [Fixed8.TryParse(10)]

            mint = token_mint(token, wallet, addr_to, asset_attachments)

            self.assertFalse(mint)

    def test_token_mint_bad_password(self):
        with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=["blah"]):
            wallet = self.GetWallet1(recreate=True)
            token = self.get_token(wallet)
            addr_to = self.wallet_1_addr

            mint = token_mint(token, wallet, addr_to)

            self.assertFalse(mint)

    def test_token_history_correct(self):
        # test Send event history
        wallet = self.GetWallet1(recreate=True)

        token, events = token_history(wallet, "NXT4")
        self.assertTrue(token)
        self.assertEqual(1, len(events))

        # test Received event history
        wallet = self.GetWallet2(recreate=True)

        token, events = token_history(wallet, "NXT4")
        self.assertTrue(token)
        self.assertEqual(1, len(events))

    def test_token_history_bad_token(self):
        wallet = self.GetWallet1(recreate=True)

        with self.assertRaises(ValueError) as context:
            token, events = token_history(wallet, "BAD")

        self.assertIn("not represent a known NEP5 token", str(context.exception))

    def test_token_serialize(self):

        wallet = self.GetWallet1(recreate=True)
        token = self.get_token(wallet)

        stream = StreamManager.GetStream()
        writer = BinaryWriter(stream)
        token.Serialize(writer)

        self.assertEqual(b'0f4e45582054656d706c617465205634044e58543408', stream.ToArray())

    def test_wallet_token(self):
        """
        Generic tests for the Token subcommand of the Wallet group
        """
        # test token no wallet
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['token']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("open a wallet", mock_print.getvalue())

        with self.OpenWallet1():
            # test token with insufficient args
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("run `token help` to see supported queries", mock_print.getvalue())

            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', None]
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("run `token help` to see supported queries", mock_print.getvalue())

            # test token with invalid subcommands
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', -1]
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("invalid parameter", mock_print.getvalue())

            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'nope']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("invalid parameter", mock_print.getvalue())

    def test_wallet_token_delete(self):
        # test wallet token with no wallet open
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['token', 'delete', 'no_wallet']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("open a wallet", mock_print.getvalue())

        with self.OpenWallet1():
            # test token delete with no parameter
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'delete']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("specify the required parameter", mock_print.getvalue())

            # test with invalid script_hash (too short)
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'delete', 'aaa']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("Invalid script hash", mock_print.getvalue())

            # test with invalid script_hash (too long)
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'delete', 20 * 'aaa']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("Invalid script hash", mock_print.getvalue())

            # test with non-existing script_hash
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'delete', '0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaab']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("Could not find a token", mock_print.getvalue())

            # finally test with a valid script_hash
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'delete', '0x31730cc9a1844891a3bafd1aa929a4142860d8d3']
                res = CommandWallet().execute(args)
                self.assertTrue(res)
                self.assertIn("deleted", mock_print.getvalue())

    def test_wallet_token_send(self):

        with self.OpenWallet1():
            # test with no parameters
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'send']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("specify the required parameter", mock_print.getvalue())

            # test with insufficient parameters
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'send', 'arg1']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("specify the required parameter", mock_print.getvalue())

            # test with too many parameters (max is 4 mandatory + 2 optional)
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'send', 'arg1', 'arg2', 'arg3', 'arg4', 'arg5', 'arg6', 'arg7']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("Too many parameters supplied", mock_print.getvalue())

            # test with invalid token argument
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'send', 'invalid_token_name', 'arg2', 'arg3', '10']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("does not represent a known NEP5 token", mock_print.getvalue())

            # test with valid token arg, but invalid from_addr
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'send', 'NXT4', 'invalid_from_addr', 'arg3', '10']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("not a valid address", mock_print.getvalue())

            # test with valid token and from_addr, but invalid to_addr
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'send', 'NXT4', 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg', 'invalid_to_addr', '10']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("not a valid address", mock_print.getvalue())

            # test with invalid amount
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'send', 'NXT4', 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg', 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg', 'invalid_amount']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("not a valid amount", mock_print.getvalue())

            # test with negative fee
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'send', 'NXT4', 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg', 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg', '10', '--fee=-0.001']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("invalid amount format", mock_print.getvalue())

            # test with weird fee
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'send', 'NXT4', 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg', 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg', '10', '--fee=0.0abc']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("invalid amount format", mock_print.getvalue())

            # Note that there is no test for invalid tx-attributes. Invalid attributes result in an empty attribute list being
            # passed to the underlying function thus having no effect.

            # test with a good transfer
            # we don't really send anything becausing testing of the internal `do_token_transfer()` already happens in `test_token_send_good()`
            # we return an object to represent the Transaction that's normally returned
            with patch('neo.Prompt.Commands.Tokens.do_token_transfer', side_effect=[object()]):
                token = self.get_token(PromptData.Wallet)
                addr_from = PromptData.Wallet.GetDefaultContract().Address
                addr_to = self.watch_addr_str

                send = token_send(PromptData.Wallet, token.symbol, addr_from, addr_to, 13)
                self.assertTrue(send)

    def test_token_history(self):
        with self.OpenWallet1():
            # test with no parameters
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'history']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("specify the required parameter", mock_print.getvalue())

            # test with unknown token
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'history', 'bad_token']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("does not represent a known NEP5 token", mock_print.getvalue())

            # test with known token (has sent event)
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'history', 'NXT4']
                res = CommandWallet().execute(args)
                self.assertTrue(res)
                self.assertIn("Sent 1000.00000000 NXT4 to AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEm", mock_print.getvalue())

        with self.OpenWallet2():
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'history', 'NXT4']
                res = CommandWallet().execute(args)
                self.assertTrue(res)
                self.assertIn("Received 1000.00000000 NXT4 from AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3", mock_print.getvalue())

    def test_wallet_token_approve(self):
        with self.OpenWallet1():
            # test with no parameters
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'approve']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("specify the required parameters", mock_print.getvalue())

            # test with insufficient parameters (1 instead of 4)
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'approve', 'arg1']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("specify the required parameter", mock_print.getvalue())

            # test with invalid token argument
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'approve', 'invalid_token_name', 'arg2', 'arg3', '10']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("does not represent a known NEP5 token", mock_print.getvalue())

            # test with valid token arg, but invalid from_addr
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'approve', 'NXT4', 'invalid_from_addr', 'arg3', '10']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("not a valid address", mock_print.getvalue())

            # test with valid token and from_addr, but invalid to_addr
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'approve', 'NXT4', 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg', 'invalid_to_addr', '10']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("not a valid address", mock_print.getvalue())

            # test with invalid amount
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'approve', 'NXT4', 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg', 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg', 'invalid_amount']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("not a valid amount", mock_print.getvalue())

            # test with negative fee
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'approve', 'NXT4', 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg', 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg', '10', '--fee=-0.001']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("invalid amount format", mock_print.getvalue())

            # test with weird fee
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'approve', 'NXT4', 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg', 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg', '10', '--fee=0.0abc']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("invalid amount format", mock_print.getvalue())

            # setup some variables that are re-used in the tests below
            token = list(PromptData.Wallet.GetTokens().values())[0]
            addr_from = PromptData.Wallet.GetDefaultContract().Address
            addr_to = self.watch_addr_str

            # test approving with invalid password
            with patch('sys.stdout', new=StringIO()) as mock_print:
                with patch('neo.Prompt.Commands.Tokens.token_get_allowance', return_value=12300000000):
                    with patch('neo.Wallets.NEP5Token.NEP5Token.TransferFrom', return_value=(self.Approve_Allowance())):
                        with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=['blah']):
                            args = ['token', 'approve', 'NXT4', addr_from, addr_to, '123']
                            res = CommandWallet().execute(args)
                            self.assertFalse(res)
                            self.assertIn("incorrect password", mock_print.getvalue())

            # test failed to approve
            with patch('sys.stdout', new=StringIO()) as mock_print:
                with patch('neo.Wallets.NEP5Token.NEP5Token.Approve', return_value=(None, None, None)):
                    args = ['token', 'approve', 'NXT4', addr_from, addr_to, '123']
                    res = CommandWallet().execute(args)
                    self.assertFalse(res)
                    self.assertIn("Failed to approve tokens", mock_print.getvalue())

            # test successful approval
            with patch('sys.stdout', new=StringIO()) as mock_print:
                with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=[self.wallet_1_pass()]):
                    args = ['token', 'approve', 'NXT4', addr_from, addr_to, '123', '--fee=0.001']
                    res = CommandWallet().execute(args)
                    self.assertTrue(res)
                    self.assertIn("Priority Fee (0.001) + Invocation Fee (0.0001) = 0.0011", mock_print.getvalue())

    def test_wallet_token_allowance(self):
        with self.OpenWallet1():
            # test with no parameters
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'allowance']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("specify the required parameters", mock_print.getvalue())

            # test with insufficient parameters (1 instead of 4)
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'allowance', 'arg1']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("specify the required parameter", mock_print.getvalue())

            # test with an invalid token argument
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'allowance', 'invalid_token_name', 'arg2', 'arg3']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("does not represent a known NEP5 token", mock_print.getvalue())

            # test with valid token arg, but invalid from_addr (as that tests exceptions from the internal _validate_nep5_args() function)
            # that function is tested enough in other command tests
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'allowance', 'NXT4', 'invalid_from_addr', 'arg3']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("not a valid address", mock_print.getvalue())

            with patch('neo.Prompt.Commands.Tokens.token_get_allowance', return_value=12300000000):
                with patch('sys.stdout', new=StringIO()) as mock_print:
                    addr_from = PromptData.Wallet.GetDefaultContract().Address
                    addr_to = self.watch_addr_str

                    args = ['token', 'allowance', 'NXT4', addr_from, addr_to]
                    res = CommandWallet().execute(args)
                    self.assertTrue(res)

    def test_token_mint(self):
        with self.OpenWallet1():
            # test with no parameters
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'mint']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("specify the required parameter", mock_print.getvalue())

            # test with insufficient parameters
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'mint', 'arg1']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("specify the required parameter", mock_print.getvalue())

            # test with too many parameters (2 mandatory, 4 optional)
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'mint', 'arg1', 'arg2', 'arg3', 'arg4', 'arg5', 'arg6', 'arg7']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("Too many parameters supplied", mock_print.getvalue())

            # test with invalid token argument
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'mint', 'invalid_token_name', 'arg2']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("does not represent a known NEP5 token", mock_print.getvalue())

            # test with invalid address
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'mint', 'NXT4', 'bad_addr']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("is not a valid address", mock_print.getvalue())

            # test with invalid --attach-neo value
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'mint', 'NXT4', 'AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y', '--attach-neo=blah']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("Could not parse value from --attach-neo", mock_print.getvalue())

            # test with invalid --attach-gas value
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'mint', 'NXT4', 'AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y', '--attach-gas=blah']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("Could not parse value from --attach-gas", mock_print.getvalue())

            # test with valid --attach-neo and attach-gas
            with patch('neo.Wallets.NEP5Token.NEP5Token.Mint') as mocked_mint:
                with patch('sys.stdout', new=StringIO()) as mock_print:
                    mocked_mint.return_value = (None, 0, None)  # tx, fee, results
                    attach_neo_arg = '--attach-neo=1'
                    attach_gas_arg = '--attach-gas=0.01'
                    args = ['token', 'mint', 'NXT4', 'AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y', attach_neo_arg, attach_gas_arg]
                    res = CommandWallet().execute(args)
                    self.assertFalse(res)
                    self.assertIn([attach_neo_arg, attach_gas_arg], mocked_mint.call_args_list[0][0])

            # test with negative fee
            with patch('sys.stdout', new=StringIO()) as mock_print:
                attach_neo_arg = '--attach-neo=1'
                fee_arg = '--fee=-0.001'
                args = ['token', 'mint', 'NXT4', 'AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y', attach_neo_arg, fee_arg]
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("invalid amount format", mock_print.getvalue())

            # test with weird fee
            with patch('sys.stdout', new=StringIO()) as mock_print:
                attach_neo_arg = '--attach-neo=1'
                fee_arg = '--fee=0.0abc'
                args = ['token', 'mint', 'NXT4', 'AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y', attach_neo_arg, fee_arg]
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("invalid amount format", mock_print.getvalue())

            # test failed minting
            with patch('neo.Wallets.NEP5Token.NEP5Token.Mint') as mocked_mint:
                with patch('sys.stdout', new=StringIO()) as mock_print:
                    mocked_mint.return_value = (object(), 0, [])  # tx, fee, results
                    args = ['token', 'mint', 'NXT4', 'AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y']
                    res = CommandWallet().execute(args)
                    self.assertFalse(res)
                    self.assertIn("Failed to mint tokens", mock_print.getvalue())

            # test wrong password
            # test working minting no password
            with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=['blah']):
                with patch('sys.stdout', new=StringIO()) as mock_print:
                    args = ['token', 'mint', 'NXT4', 'AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y']
                    res = CommandWallet().execute(args)
                    self.assertIn("incorrect password", mock_print.getvalue())

            # test working minting
            with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=[self.wallet_1_pass()]):
                with patch('sys.stdout', new=StringIO()) as mock_print:
                    args = ['token', 'mint', 'NXT4', 'AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y', '--fee=0.001', '--tx-attr={"usage":241,"data":"This is a remark"}']
                    res = CommandWallet().execute(args)
                    self.assertTrue(res)
                    self.assertIn("[NXT4] Will mint tokens to address", mock_print.getvalue())
                    self.assertIn("Priority Fee (0.001) + Invocation Fee (0.0001) = 0.0011", mock_print.getvalue())

    def test_token_register(self):
        with self.OpenWallet1():
            # test token delete with no parameter
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'register']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("specify the required parameter", mock_print.getvalue())

            # test token delete with insufficient parameters
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'register', 'arg1']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("specify the required parameter", mock_print.getvalue())

            # test with invalid token argument
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'register', 'invalid_token_name', 'arg2']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("does not represent a known NEP5 token", mock_print.getvalue())

            # test with invalid address
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'register', 'NXT4', 'bad_addr']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("is not a valid address", mock_print.getvalue())

            # test with negative fee
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'register', 'NXT4', 'AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y', '--fee=-0.001']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("invalid amount format", mock_print.getvalue())

            # test with weird fee
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'register', 'NXT4', 'AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y', '--fee=0.0abc']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("invalid amount format", mock_print.getvalue())

            # test with some exception in NEP5Token.CrowdsaleRegister
            with patch('neo.Wallets.NEP5Token.NEP5Token.CrowdsaleRegister') as mocked_register:
                with patch('sys.stdout', new=StringIO()) as mock_print:
                    mocked_register.return_value = (object(), 0, [])  # tx, fee, results
                    args = ['token', 'register', 'NXT4', 'AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y']
                    res = CommandWallet().execute(args)
                    self.assertFalse(res)
                    self.assertIn("Could not register address(es)", mock_print.getvalue())

            # test with bad password
            with patch('sys.stdout', new=StringIO()) as mock_print:
                with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=["blah"]):
                    args = ['token', 'register', 'NXT4', 'AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y']
                    res = CommandWallet().execute(args)
                    self.assertFalse(res)
                    self.assertIn("incorrect password", mock_print.getvalue())

            # test with valid address
            with patch('sys.stdout', new=StringIO()) as mock_print:
                with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=[self.wallet_1_pass()]):
                    args = ['token', 'register', 'NXT4', 'AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y', '--fee=0.001']
                    res = CommandWallet().execute(args)
                    self.assertTrue(res)
                    self.assertIn("[NXT4] Will register addresses", mock_print.getvalue())
                    self.assertIn("Priority Fee (0.001) + Invocation Fee (0.0001) = 0.0011", mock_print.getvalue())

    # utility function
    def Approve_Allowance(self):
        wallet = self.GetWallet1(recreate=True)
        approve_from = self.wallet_1_addr
        approve_to = self.watch_addr_str
        tokens = self.get_token(wallet)
        token = get_asset_id(wallet, tokens.symbol)
        amount = amount_from_string(token, "123")

        tx, fee, results = token.Approve(wallet, approve_from, approve_to, amount)

        return tx, fee, results

    # utility function
    def get_token(self, wallet):
        return list(wallet.GetTokens().values())[0]


class TokenSendFromTestCase(WalletFixtureTestCase):
    """
    Moved tests into separate class because some of the tests in the above "UserWalletTestCase" appear to modify the blockchain state
    or deplete our funds causing the good sending test to fail.
    """
    watch_addr_str = 'AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEm'
    wallet_1_addr = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # replace the prompt_toolkit formatted print function with the default such that we can test easily
        pp.printer = print

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        pp.reset_printer()

    @contextmanager
    def OpenWallet1(self):
        PromptData.Wallet = UserWalletTestCase.GetWallet1(recreate=True)

        yield

        filename = UserWalletTestCase.wallet_1_dest()
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except OSError:
                pass
        PromptData.Wallet = None

    def test_wallet_token_sendfrom(self):
        with self.OpenWallet1():
            # test with no parameters
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'sendfrom']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("specify the required parameter", mock_print.getvalue())

            # test with insufficient parameters
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'sendfrom', 'arg1']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("specify the required parameter", mock_print.getvalue())

            # test with invalid token argument
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'sendfrom', 'invalid_token_name', 'arg2', 'arg3', '10']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("does not represent a known NEP5 token", mock_print.getvalue())

            # test with valid token arg, but invalid from_addr
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'sendfrom', 'NXT4', 'invalid_from_addr', 'arg3', '10']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("not a valid address", mock_print.getvalue())

            # test with valid token and from_addr, but invalid to_addr
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'sendfrom', 'NXT4', 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg', 'invalid_to_addr', '10']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("not a valid address", mock_print.getvalue())

            # test with invalid amount
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'sendfrom', 'NXT4', 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg', 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg', 'invalid_amount']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("not a valid amount", mock_print.getvalue())

            # test with negative fee
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'sendfrom', 'NXT4', 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg', 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg', '10', '--fee=-0.001']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("invalid amount format", mock_print.getvalue())

            # test with weird fee
            with patch('sys.stdout', new=StringIO()) as mock_print:
                args = ['token', 'sendfrom', 'NXT4', 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg', 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg', '10', '--fee=0.0abc']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("invalid amount format", mock_print.getvalue())

            # setup some variables that are re-used in the tests below
            token = list(PromptData.Wallet.GetTokens().values())[0]
            addr_from = PromptData.Wallet.GetDefaultContract().Address
            addr_to = self.watch_addr_str

            # test sending with invalid password
            with patch('sys.stdout', new=StringIO()) as mock_print:
                with patch('neo.Prompt.Commands.Tokens.token_get_allowance', return_value=12300000000):
                    with patch('neo.Wallets.NEP5Token.NEP5Token.TransferFrom', return_value=(self.Approve_Allowance(PromptData.Wallet, token))):
                        with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=['blah']):
                            args = ['token', 'sendfrom', 'NXT4', addr_from, addr_to, '123']
                            res = CommandWallet().execute(args)
                            self.assertFalse(res)
                            self.assertIn("incorrect password", mock_print.getvalue())

            # test sending something where the test run fails
            with patch('sys.stdout', new=StringIO()) as mock_print:
                exception_msg = "totally not expected error"
                with patch('neo.Prompt.Commands.Tokens.test_token_send_from', side_effect=[Exception(exception_msg)]):
                    error_level = 30
                    with self.assertLogHandler('generic', error_level) as logs:
                        # the args don't really matter, except for the first 2
                        args = ['token', 'sendfrom', 'NXT4', addr_from, addr_to, '123']
                        res = CommandWallet().execute(args)
                        self.assertFalse(res)
                        self.assertIn("Something really unexpected happened", mock_print.getvalue())
                        self.assertIn(exception_msg, logs.output[0])

            # test having the VM fail by returning None
            with patch('sys.stdout', new=StringIO()) as mock_print:
                with patch('neo.Prompt.Commands.Tokens.test_token_send_from', side_effect=[(None, None, None, None)]):
                    # the args don't really matter, except for the first 2
                    args = ['token', 'sendfrom', 'NXT4', addr_from, addr_to, '123']
                    res = CommandWallet().execute(args)
                    self.assertFalse(res)
                    self.assertIn("no Transaction object or VM output", mock_print.getvalue())

            # test having the VM fail by returning a result that it not 1
            with patch('sys.stdout', new=StringIO()) as mock_print:
                bad_vm_result = [StackItem.New(0)]
                fake_tx = object()
                fake_fee = 111
                with patch('neo.Prompt.Commands.Tokens.test_token_send_from', side_effect=[(None, fake_tx, fake_fee, bad_vm_result)]):
                    # the args don't really matter, except for the first 2
                    args = ['token', 'sendfrom', 'NXT4', addr_from, addr_to, '123']
                    res = CommandWallet().execute(args)
                    self.assertFalse(res)
                    self.assertIn("Virtual machine returned: 0", mock_print.getvalue())

            # test sending with insufficient allowance
            with patch('sys.stdout', new=StringIO()) as mock_print:
                res = CommandWallet().execute(['token', 'sendfrom', token.symbol, addr_from, addr_to, '10000000'])
                self.assertFalse(res)
                self.assertIn("Insufficient allowance", mock_print.getvalue())

            # successful test
            with patch('sys.stdout', new=StringIO()) as mock_print:
                with patch('neo.Prompt.Commands.Tokens.token_get_allowance', return_value=12300000000):
                    with patch('neo.Wallets.NEP5Token.NEP5Token.TransferFrom', return_value=self.Approve_Allowance(PromptData.Wallet, token)):
                        with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=[self.wallet_1_pass()]):
                            args = ['token', 'sendfrom', 'NXT4', addr_from, addr_to, '123', '--fee=0.001']
                            res = CommandWallet().execute(args)
                            self.assertTrue(res)
                            self.assertIn("Priority Fee (0.001) + Transfer Fee (0.0001) = 0.0011", mock_print.getvalue())

    def Approve_Allowance(self, wallet, token):
        approve_from = self.wallet_1_addr
        approve_to = self.watch_addr_str
        amount = amount_from_string(token, "123")

        tx, fee, results = token.Approve(wallet, approve_from, approve_to, amount)

        return tx, fee, results
