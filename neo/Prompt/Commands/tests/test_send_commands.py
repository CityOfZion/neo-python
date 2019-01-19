from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Wallets.utils import to_aes_key
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Core.Blockchain import Blockchain
from neocore.UInt160 import UInt160
from neo.Prompt.Commands.WalletImport import ImportToken
from neo.Prompt.Utils import get_tx_attr_from_args
from neo.Prompt.Commands import Send, Wallet
from neo.Prompt.PromptData import PromptData
import shutil
from mock import patch, MagicMock
import json
from io import StringIO
from neo.Prompt.PromptPrinter import pp


class UserWalletTestCase(WalletFixtureTestCase):
    wallet_1_script_hash = UInt160(data=b'\x1c\xc9\xc0\\\xef\xff\xe6\xcd\xd7\xb1\x82\x81j\x91R\xec!\x8d.\xc0')

    wallet_1_addr = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'

    import_watch_addr = UInt160(data=b'\x08t/\\P5\xac-\x0b\x1c\xb4\x94tIyBu\x7f1*')
    watch_addr_str = 'AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEm'
    _wallet1 = None

    wallet_2_addr = 'AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEm'
    _wallet2 = None

    wallet_3_addr = 'AZiE7xfyJALW7KmADWtCJXGGcnduYhGiCX'
    _wallet3 = None

    wallet_2_and_3_multisig_addr = "Aau2M4UdXxwxLLizDw11eDZRDs5jpXduh8"

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

    @classmethod
    def tearDown(cls):
        PromptData.Wallet = None

    def test_send_neo(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
                PromptData.Wallet = self.GetWallet1(recreate=True)
                args = ['send', 'neo', self.watch_addr_str, '1']

                res = Wallet.CommandWallet().execute(args)

                self.assertTrue(res)
                self.assertIn("Sending with fee: 0.0", mock_print.getvalue())

    def test_send_gas(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
                PromptData.Wallet = self.GetWallet1(recreate=True)
                args = ['send', 'gas', self.watch_addr_str, '1']

                res = Wallet.CommandWallet().execute(args)

                self.assertTrue(res)
                self.assertIn("Sending with fee: 0.0", mock_print.getvalue())

    def test_send_with_fee_and_from_addr(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
                PromptData.Wallet = self.GetWallet1(recreate=True)
                args = ['send', 'neo', self.watch_addr_str, '1', '--from-addr=AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3', '--fee=0.005']

                res = Wallet.CommandWallet().execute(args)

                self.assertTrue(res)  # verify successful tx

                json_res = res.ToJson()
                self.assertEqual(self.watch_addr_str, json_res['vout'][0]['address'])  # verify correct address_to
                self.assertEqual(self.wallet_1_addr, json_res['vout'][1]['address'])  # verify correct address_from
                self.assertEqual(json_res['net_fee'], "0.005")  # verify correct fee
                self.assertIn("Sending with fee: 0.005", mock_print.getvalue())

    def test_send_no_wallet(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ["send", "neo", self.wallet_1_addr, '5']

            Wallet.CommandWallet().execute(args)

            self.assertIn("Please open a wallet", mock_print.getvalue())

    def test_send_bad_args(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            PromptData.Wallet = self.GetWallet1(recreate=True)
            args = ['send', 'neo', self.watch_addr_str]  # too few args

            res = Wallet.CommandWallet().execute(args)

            self.assertFalse(res)
            self.assertIn("Please specify the required parameters", mock_print.getvalue())

    def test_send_bad_assetid(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            PromptData.Wallet = self.GetWallet1(recreate=True)
            args = ['send', 'blah', self.watch_addr_str, '12']

            res = Wallet.CommandWallet().execute(args)

            self.assertFalse(res)
            self.assertIn("Asset id not found", mock_print.getvalue())

    def test_send_bad_address_to(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            PromptData.Wallet = self.GetWallet1(recreate=True)
            address_to = 'AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkE'  # address_to is too short causing ToScriptHash to fail
            args = ['send', 'neo', address_to, '12']

            res = Wallet.CommandWallet().execute(args)

            self.assertFalse(res)
            self.assertIn("Not correct Address, wrong length", mock_print.getvalue())

    def test_send_bad_address_from(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            PromptData.Wallet = self.GetWallet1(recreate=True)
            address_from = '--from-addr=AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc'  # address_from is too short causing ToScriptHash to fail
            args = ['send', 'neo', self.watch_addr_str, '12', address_from]

            res = Wallet.CommandWallet().execute(args)

            self.assertFalse(res)
            self.assertIn("Not correct Address, wrong length", mock_print.getvalue())

    def test_send_negative_amount(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            PromptData.Wallet = self.GetWallet1(recreate=True)
            args = ['send', 'neo', self.watch_addr_str, '-12']

            res = Wallet.CommandWallet().execute(args)

            self.assertFalse(res)
            self.assertIn("invalid amount format", mock_print.getvalue())

    def test_send_zero_amount(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            PromptData.Wallet = self.GetWallet1(recreate=True)
            args = ['send', 'neo', self.watch_addr_str, '0']

            res = Wallet.CommandWallet().execute(args)

            self.assertFalse(res)
            self.assertIn("Amount cannot be 0", mock_print.getvalue())

    def test_send_weird_amount(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            PromptData.Wallet = self.GetWallet1(recreate=True)
            args = ['send', 'neo', self.watch_addr_str, '12.abc3']

            res = Wallet.CommandWallet().execute(args)

            self.assertFalse(res)
            self.assertIn("invalid amount format", mock_print.getvalue())

    def test_send_bad_precision_amount(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            PromptData.Wallet = self.GetWallet1(recreate=True)
            args = ['send', 'neo', self.watch_addr_str, '12.01']

            res = Wallet.CommandWallet().execute(args)

            self.assertFalse(res)
            self.assertIn("incorrect amount precision", mock_print.getvalue())

    def test_send_negative_fee(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            PromptData.Wallet = self.GetWallet1(recreate=True)
            args = ['send', 'neo', self.watch_addr_str, '12', '--fee=-0.005']

            res = Wallet.CommandWallet().execute(args)

            self.assertFalse(res)
            self.assertIn("invalid amount format", mock_print.getvalue())

    def test_send_weird_fee(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            PromptData.Wallet = self.GetWallet1(recreate=True)
            args = ['send', 'neo', self.watch_addr_str, '12', '--fee=0.0abc']

            res = Wallet.CommandWallet().execute(args)

            self.assertFalse(res)
            self.assertIn("invalid amount format", mock_print.getvalue())

    def test_send_token_bad(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            PromptData.Wallet = self.GetWallet1(recreate=True)

            token_hash = 'f8d448b227991cf07cb96a6f9c0322437f1599b9'
            ImportToken(PromptData.Wallet, token_hash)

            args = ['send', 'NEP5', self.watch_addr_str, '32']

            res = Wallet.CommandWallet().execute(args)

            self.assertFalse(res)
            self.assertIn("Could not find the contract hash", mock_print.getvalue())

    def test_send_token_ok(self):
        with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            with patch('sys.stdout', new=StringIO()) as mock_print:
                PromptData.Wallet = self.GetWallet1(recreate=True)

                token_hash = '31730cc9a1844891a3bafd1aa929a4142860d8d3'
                ImportToken(PromptData.Wallet, token_hash)

                args = ['send', 'NXT4', self.watch_addr_str, '30', '--from-addr=%s' % self.wallet_1_addr]

                res = Wallet.CommandWallet().execute(args)

                self.assertTrue(res)
                self.assertIn("Will transfer 30.00000000 NXT4 from AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3 to AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEm",
                              mock_print.getvalue())

    def test_insufficient_funds(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            PromptData.Wallet = self.GetWallet1(recreate=True)
            args = ['send', 'gas', self.watch_addr_str, '72620']

            res = Wallet.CommandWallet().execute(args)

            self.assertFalse(res)
            self.assertIn("Insufficient funds", mock_print.getvalue())

    def test_bad_password(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=['blah']):
            with patch('sys.stdout', new=StringIO()) as mock_print:
                PromptData.Wallet = self.GetWallet1(recreate=True)
                args = ['send', 'neo', self.watch_addr_str, '50']

                res = Wallet.CommandWallet().execute(args)

                self.assertFalse(res)
                self.assertIn("Incorrect password", mock_print.getvalue())

    @patch.object(Send, 'gather_signatures')
    def test_owners(self, mock):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            PromptData.Wallet = self.GetWallet1(recreate=True)

            args = ['send', 'gas', self.wallet_1_addr, '2', "--owners=['AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK','APRgMZHZubii29UXF9uFa6sohrsYupNAvx']"]

            Wallet.CommandWallet().execute(args)

            self.assertTrue(mock.called)

    def test_attributes(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            PromptData.Wallet = self.GetWallet1(recreate=True)
            args = ['send', 'gas', self.watch_addr_str, '2', '--tx-attr={"usage":241,"data":"This is a remark"}']

            res = Wallet.CommandWallet().execute(args)

            self.assertTrue(res)
            self.assertEqual(2, len(
                res.Attributes))  # By default the script_hash of the transaction sender is added to the TransactionAttribute list, therefore the Attributes length is `count` + 1

    def test_multiple_attributes(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            PromptData.Wallet = self.GetWallet1(recreate=True)
            args = ['send', 'gas', self.watch_addr_str, '2', '--tx-attr=[{"usage":241,"data":"This is a remark"},{"usage":242,"data":"This is a remark 2"}]']

            res = Wallet.CommandWallet().execute(args)

            self.assertTrue(res)
            self.assertEqual(3, len(res.Attributes))

    def test_bad_attributes(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            PromptData.Wallet = self.GetWallet1(recreate=True)
            args = ['send', 'gas', self.watch_addr_str, '2', '--tx-attr=[{"usa:241"data":his is a remark"}]']

            res = Wallet.CommandWallet().execute(args)

            self.assertTrue(res)
            self.assertEqual(1, len(res.Attributes))

    def test_utils_attr_str(self):

        args = ["--tx-attr=[{'usa:241'data':his is a remark'}]"]

        with self.assertRaises(Exception) as context:
            args, txattrs = get_tx_attr_from_args(args)

            self.assertTrue('could not convert object' in context.exception)
        self.assertEqual(len(args), 0)
        self.assertEqual(len(txattrs), 0)

    def test_utilst_bad_type(self):

        args = ["--tx-attr=bytearray(b'\x00\x00')"]

        with self.assertRaises(Exception) as context:
            args, txattr = get_tx_attr_from_args(args)
            self.assertTrue('could not convert object' in context.exception)
        self.assertEqual(len(args), 0)
        self.assertEqual(len(txattr), 0)

    def test_fails_to_sign_tx(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            with patch('neo.Wallets.Wallet.Wallet.Sign', return_value=False):
                with patch('sys.stdout', new=StringIO()) as mock_print:
                    PromptData.Wallet = self.GetWallet1(recreate=True)
                    args = ['send', 'gas', self.watch_addr_str, '2']

                    res = Wallet.CommandWallet().execute(args)

                    self.assertFalse(res)
                    self.assertIn(
                        "Transaction initiated, but the signature is incomplete. Use the `sign` command with the information below to complete signing",
                        mock_print.getvalue())

    def test_fails_to_relay_tx(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            with patch('neo.Prompt.Commands.Send.NodeLeader.Relay', return_value=False):
                with patch('sys.stdout', new=StringIO()) as mock_print:
                    PromptData.Wallet = self.GetWallet1(recreate=True)
                    args = ['send', 'gas', self.watch_addr_str, '2']

                    res = Wallet.CommandWallet().execute(args)

                    self.assertFalse(res)
                    self.assertIn("Could not relay tx", mock_print.getvalue())

    def test_could_not_send(self):
        # mocking traceback module to avoid stacktrace printing during test run
        with patch('neo.Prompt.Commands.Send.traceback'):
            with patch('sys.stdout', new=StringIO()) as mock_print:
                with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
                    with patch('neo.Wallets.Wallet.Wallet.GetStandardAddress', side_effect=[Exception]):
                        PromptData.Wallet = self.GetWallet1(recreate=True)
                        args = ['send', 'gas', self.watch_addr_str, '2']
                        res = Wallet.CommandWallet().execute(args)

                        self.assertFalse(res)
                        self.assertIn("Could not send:", mock_print.getvalue())

    def test_sendmany_good_simple(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Send.prompt',
                       side_effect=["neo", self.watch_addr_str, "1", "gas", self.watch_addr_str, "1", UserWalletTestCase.wallet_1_pass()]):
                PromptData.Wallet = self.GetWallet1(recreate=True)
                args = ['sendmany', '2']

                res = Wallet.CommandWallet().execute(args)

                self.assertTrue(res)  # verify successful tx
                self.assertIn("Sending with fee: 0.0", mock_print.getvalue())
                json_res = res.ToJson()

                # check for 2 transfers
                transfers = 0
                for info in json_res['vout']:
                    if info['address'] == self.watch_addr_str:
                        transfers += 1
                self.assertEqual(2, transfers)

    def test_sendmany_good_complex(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Send.prompt',
                       side_effect=["neo", "AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK", "1", "gas", "AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK", "1",
                                    UserWalletTestCase.wallet_1_pass()]):
                PromptData.Wallet = self.GetWallet1(recreate=True)
                args = ['sendmany', '2', '--from-addr=%s' % self.wallet_1_addr, '--change-addr=%s' % self.watch_addr_str, '--fee=0.005']

                address_from_account_state = Blockchain.Default().GetAccountState(self.wallet_1_addr).ToJson()
                address_from_gas = next(filter(lambda b: b['asset'] == '0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7',
                                               address_from_account_state['balances']))
                address_from_gas_bal = address_from_gas['value']

                res = Wallet.CommandWallet().execute(args)

                self.assertTrue(res)  # verify successful tx

                json_res = res.ToJson()
                self.assertEqual("AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK", json_res['vout'][0]['address'])  # verify correct address_to
                self.assertEqual(self.watch_addr_str, json_res['vout'][2]['address'])  # verify correct change address
                self.assertEqual(float(address_from_gas_bal) - 1 - 0.005, float(json_res['vout'][3]['value']))
                self.assertEqual('0.005', json_res['net_fee'])
                self.assertIn("Sending with fee: 0.005", mock_print.getvalue())

    def test_sendmany_no_wallet(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['sendmany', '2']

            Wallet.CommandWallet().execute(args)

            self.assertIn("Please open a wallet", mock_print.getvalue())

    def test_sendmany_bad_args(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            PromptData.Wallet = self.GetWallet1(recreate=True)
            args = ['sendmany']  # too few args

            res = Wallet.CommandWallet().execute(args)

            self.assertFalse(res)
            self.assertIn("Please specify the required parameter", mock_print.getvalue())

    def test_sendmany_bad_outgoing(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            PromptData.Wallet = self.GetWallet1(recreate=True)
            args = ['sendmany', '0']  # too few outgoing

            res = Wallet.CommandWallet().execute(args)

            self.assertFalse(res)
            self.assertIn("Outgoing number must be >= 1", mock_print.getvalue())

    def test_sendmany_weird_outgoing(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            PromptData.Wallet = self.GetWallet1(recreate=True)
            args = ['sendmany', '0.5']  # weird number outgoing

            res = Wallet.CommandWallet().execute(args)

            self.assertFalse(res)
            self.assertIn("Invalid outgoing number", mock_print.getvalue())

    def test_sendmany_bad_assetid(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Send.prompt', side_effect=["neo", self.watch_addr_str, "1", "blah", self.watch_addr_str, "1"]):
                PromptData.Wallet = self.GetWallet1(recreate=True)
                args = ['sendmany', '2']

                res = Wallet.CommandWallet().execute(args)

                self.assertFalse(res)
                self.assertIn("Asset id not found", mock_print.getvalue())

    def test_sendmany_token(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Send.prompt', side_effect=["neo", self.watch_addr_str, "1", "NXT4", self.watch_addr_str, "32"]):
                PromptData.Wallet = self.GetWallet1(recreate=True)

                token_hash = '31730cc9a1844891a3bafd1aa929a4142860d8d3'
                ImportToken(PromptData.Wallet, token_hash)

                args = ['sendmany', "2", '--from-addr=%s' % self.wallet_1_addr]

                res = Wallet.CommandWallet().execute(args)

                self.assertFalse(res)
                self.assertIn("sendmany does not support NEP5 tokens", mock_print.getvalue())

    def test_sendmany_bad_address_to(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Send.prompt',
                       side_effect=["neo", self.watch_addr_str, "1", "gas", "AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkE", "1"]):  # address is too short

                PromptData.Wallet = self.GetWallet1(recreate=True)
                args = ['sendmany', '2']

                res = Wallet.CommandWallet().execute(args)

                self.assertFalse(res)
                self.assertIn("Not correct Address, wrong length", mock_print.getvalue())

    def test_sendmany_negative_amount(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Send.prompt', side_effect=["neo", self.watch_addr_str, "1", "gas", self.watch_addr_str, "-1"]):
                PromptData.Wallet = self.GetWallet1(recreate=True)
                args = ['sendmany', '2']

                res = Wallet.CommandWallet().execute(args)

                self.assertFalse(res)
                self.assertIn("invalid amount format", mock_print.getvalue())

    def test_sendmany_zero_amount(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Send.prompt', side_effect=["neo", self.watch_addr_str, "1", "gas", self.watch_addr_str, "0"]):
                PromptData.Wallet = self.GetWallet1(recreate=True)
                args = ['sendmany', '2']

                res = Wallet.CommandWallet().execute(args)

                self.assertFalse(res)
                self.assertIn("Amount cannot be 0", mock_print.getvalue())

    def test_sendmany_weird_amount(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Send.prompt', side_effect=["neo", self.watch_addr_str, "1", "gas", self.watch_addr_str, "5.abc3"]):
                PromptData.Wallet = self.GetWallet1(recreate=True)
                args = ['sendmany', '2']

                res = Wallet.CommandWallet().execute(args)

                self.assertFalse(res)
                self.assertIn("invalid amount format", mock_print.getvalue())

    def test_sendmany_bad_precision_amount(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Send.prompt', side_effect=["gas", self.watch_addr_str, "1", "neo", self.watch_addr_str, "5.01"]):
                PromptData.Wallet = self.GetWallet1(recreate=True)
                args = ['sendmany', '2']

                res = Wallet.CommandWallet().execute(args)

                self.assertFalse(res)
                self.assertIn("incorrect amount precision", mock_print.getvalue())

    def test_sendmany_bad_address_from(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Send.prompt', side_effect=["neo", self.watch_addr_str, "1", "gas", self.watch_addr_str, "1"]):
                PromptData.Wallet = self.GetWallet1(recreate=True)
                address_from = '--from-addr=AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc'  # address_from is too short causing ToScriptHash to fail
                args = ['sendmany', '2', address_from]

                res = Wallet.CommandWallet().execute(args)

                self.assertFalse(res)
                self.assertIn("Not correct Address, wrong length", mock_print.getvalue())

    def test_sendmany_bad_change_address(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Send.prompt', side_effect=["neo", self.watch_addr_str, "1", "gas", self.watch_addr_str, "1"]):
                PromptData.Wallet = self.GetWallet1(recreate=True)
                change_address = '--change-addr=AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkE'  # change address is too short causing ToScriptHash to fail
                args = ['sendmany', '2', change_address]

                res = Wallet.CommandWallet().execute(args)

                self.assertFalse(res)
                self.assertIn("Not correct Address, wrong length", mock_print.getvalue())

    def test_sendmany_negative_fee(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Send.prompt', side_effect=["neo", self.watch_addr_str, "1", "gas", self.watch_addr_str, "1"]):
                PromptData.Wallet = self.GetWallet1(recreate=True)
                args = ['sendmany', '2', '--fee=-0.005']

                res = Wallet.CommandWallet().execute(args)

                self.assertFalse(res)
                self.assertIn("invalid amount format", mock_print.getvalue())

    def test_sendmany_keyboard_interrupt(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Send.prompt', side_effect=["neo", self.watch_addr_str, "1", "gas", KeyboardInterrupt]):
                PromptData.Wallet = self.GetWallet1(recreate=True)
                args = ['sendmany', '2']

                res = Wallet.CommandWallet().execute(args)

                self.assertFalse(res)
                self.assertIn("Transaction cancelled", mock_print.getvalue())

    def test_parse_and_sign_good(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_2_pass()]):
            # start the tx from wallet2
            PromptData.Wallet = self.GetWallet2(recreate=True)
            args = ['send', 'neo', self.wallet_1_addr, '1', '--from-addr=' + self.wallet_2_and_3_multisig_addr]

            Wallet.CommandWallet().execute(args)

            # now sign the tx with wallet3
            PromptData.Wallet = self.GetWallet3(recreate=True)
            jsn = '{"type":"Neo.Core.ContractTransaction","hex":"800000014405fd5ae29ceeb20912776048c544109c8c67c4128c019863eca58cf677ad360000029b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f505000000001cc9c05cefffe6cdd7b182816a9152ec218d2ec09b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc50084d71700000000d1c4904014bfe7d34e9e97370f2cd3a633377cd6","items":{"0xd67c3733a6d32c0f37979e4ed3e7bf144090c4d1":{"script":"522103989f7417da540a8ce00195738249291cba058102a12d2df1b00e2a826d8bd0612103c46aec8d1ac8cb58fe74764de223d15e7045de67a51d1a4bcecd396918e9603452ae","parameters":[{"type":"Signature"},{"type":"Signature"}],"signatures":{"03c46aec8d1ac8cb58fe74764de223d15e7045de67a51d1a4bcecd396918e96034":"b5b32d6b56f3729747380072c722c50b0ee91e930f58a58d49c98c5543e335b70f6a400c8e1f9fa9653f7605ad229974cacfac3143cd355ca900c328b3db6018"}}}}'
            args = ['sign', jsn]

            res = Wallet.CommandWallet().execute(args)

            res = res.ToJson()
            self.assertTrue(res)
            self.assertEqual(res['vout'][0]['value'], "1")  # verify the amount
            self.assertEqual(res['vout'][0]['address'], self.wallet_1_addr)  # verify to_address
            self.assertEqual(res['vout'][1]['address'], self.wallet_2_and_3_multisig_addr)  # verify from_address

    def test_parse_and_sign_bad_jsn(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_2_pass()]):
                # start the tx from wallet2
                PromptData.Wallet = self.GetWallet2(recreate=True)
                args = ['send', 'neo', self.wallet_1_addr, '1', '--from-addr=' + self.wallet_2_and_3_multisig_addr]

                Wallet.CommandWallet().execute(args)

                # now sign the tx with wallet3
                PromptData.Wallet = self.GetWallet3(recreate=True)
                jsn = 'blah'
                args = ['sign', jsn]

                res = Wallet.CommandWallet().execute(args)

                self.assertFalse(res)
                self.assertIn("Failed to parse JSON", mock_print.getvalue())

    def test_parse_and_sign_fails_to_relay(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_2_pass()]):
                with patch('neo.Prompt.Commands.Send.NodeLeader.Relay', return_value=False):
                    # start the tx from wallet2
                    PromptData.Wallet = self.GetWallet2(recreate=True)
                    args = ['send', 'neo', self.wallet_1_addr, '1', '--from-addr=' + self.wallet_2_and_3_multisig_addr]

                    Wallet.CommandWallet().execute(args)

                    # now sign the tx with wallet3
                    PromptData.Wallet = self.GetWallet3(recreate=True)
                    jsn = '{"type":"Neo.Core.ContractTransaction","hex":"800000014405fd5ae29ceeb20912776048c544109c8c67c4128c019863eca58cf677ad360000029b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f505000000001cc9c05cefffe6cdd7b182816a9152ec218d2ec09b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc50084d71700000000d1c4904014bfe7d34e9e97370f2cd3a633377cd6","items":{"0xd67c3733a6d32c0f37979e4ed3e7bf144090c4d1":{"script":"522103989f7417da540a8ce00195738249291cba058102a12d2df1b00e2a826d8bd0612103c46aec8d1ac8cb58fe74764de223d15e7045de67a51d1a4bcecd396918e9603452ae","parameters":[{"type":"Signature"},{"type":"Signature"}],"signatures":{"03c46aec8d1ac8cb58fe74764de223d15e7045de67a51d1a4bcecd396918e96034":"b5b32d6b56f3729747380072c722c50b0ee91e930f58a58d49c98c5543e335b70f6a400c8e1f9fa9653f7605ad229974cacfac3143cd355ca900c328b3db6018"}}}}'
                    args = ['sign', jsn]

                    res = Wallet.CommandWallet().execute(args)

                    self.assertFalse(res)
                    self.assertIn("Could not relay tx", mock_print.getvalue())

    def test_parse_and_sign_twice(self):  # this test implies there are more signatures needed
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_2_pass()]):
                # start the tx from wallet2
                PromptData.Wallet = self.GetWallet2(recreate=True)
                args = ['send', 'neo', self.wallet_1_addr, '1', '--from-addr=' + self.wallet_2_and_3_multisig_addr]

                Wallet.CommandWallet().execute(args)

                # now sign the tx with wallet2 again
                jsn = '{"type":"Neo.Core.ContractTransaction","hex":"800000014405fd5ae29ceeb20912776048c544109c8c67c4128c019863eca58cf677ad360000029b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f505000000001cc9c05cefffe6cdd7b182816a9152ec218d2ec09b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc50084d71700000000d1c4904014bfe7d34e9e97370f2cd3a633377cd6","items":{"0xd67c3733a6d32c0f37979e4ed3e7bf144090c4d1":{"script":"522103989f7417da540a8ce00195738249291cba058102a12d2df1b00e2a826d8bd0612103c46aec8d1ac8cb58fe74764de223d15e7045de67a51d1a4bcecd396918e9603452ae","parameters":[{"type":"Signature"},{"type":"Signature"}],"signatures":{"03c46aec8d1ac8cb58fe74764de223d15e7045de67a51d1a4bcecd396918e96034":"b5b32d6b56f3729747380072c722c50b0ee91e930f58a58d49c98c5543e335b70f6a400c8e1f9fa9653f7605ad229974cacfac3143cd355ca900c328b3db6018"}}}}'
                args = ['sign', jsn]

                res = Wallet.CommandWallet().execute(args)

                self.assertFalse(res)
                self.assertIn("Transaction initiated, but the signature is incomplete", mock_print.getvalue())

    def test_parse_and_sign_exception(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_2_pass()]):
                with patch('neo.Prompt.Commands.Send.traceback'):  # mocking traceback module to avoid stacktrace printing during test run
                    # start the tx from wallet2
                    PromptData.Wallet = self.GetWallet2(recreate=True)
                    args = ['send', 'neo', self.wallet_1_addr, '1', '--from-addr=' + self.wallet_2_and_3_multisig_addr]

                    Wallet.CommandWallet().execute(args)

                    # mocking wallet to trigger the exception
                    PromptData.Wallet = MagicMock()
                    PromptData.Wallet.Sign.side_effect = Exception
                    jsn = '{"type":"Neo.Core.ContractTransaction","hex":"800000014405fd5ae29ceeb20912776048c544109c8c67c4128c019863eca58cf677ad360000029b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f505000000001cc9c05cefffe6cdd7b182816a9152ec218d2ec09b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc50084d71700000000d1c4904014bfe7d34e9e97370f2cd3a633377cd6","items":{"0xd67c3733a6d32c0f37979e4ed3e7bf144090c4d1":{"script":"522103989f7417da540a8ce00195738249291cba058102a12d2df1b00e2a826d8bd0612103c46aec8d1ac8cb58fe74764de223d15e7045de67a51d1a4bcecd396918e9603452ae","parameters":[{"type":"Signature"},{"type":"Signature"}],"signatures":{"03c46aec8d1ac8cb58fe74764de223d15e7045de67a51d1a4bcecd396918e96034":"b5b32d6b56f3729747380072c722c50b0ee91e930f58a58d49c98c5543e335b70f6a400c8e1f9fa9653f7605ad229974cacfac3143cd355ca900c328b3db6018"}}}}'
                    args = ['sign', jsn]

                    res = Wallet.CommandWallet().execute(args)

                    self.assertFalse(res)
                    self.assertIn("Could not send:", mock_print.getvalue())

    def test_parse_and_sign_no_args(self):
        with patch('sys.stdout', new=StringIO()) as mock_print:
            PromptData.Wallet = self.GetWallet2(recreate=True)
            args = ['sign']

            res = Wallet.CommandWallet().execute(args)

            self.assertFalse(res)
            self.assertIn("Please specify the required parameter", mock_print.getvalue())
