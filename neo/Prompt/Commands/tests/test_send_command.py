from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Wallets.utils import to_aes_key
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Core.Blockchain import Blockchain
from neocore.UInt160 import UInt160
from neo.Prompt.Commands.Send import construct_send_basic, construct_send_many, process_transaction
from neo.Prompt.Commands.Wallet import ImportToken
from neo.Prompt.Utils import get_tx_attr_from_args
from neo.Prompt.Commands import Send
import shutil
from mock import MagicMock
import json

from mock import patch


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
            shutil.copyfile(cls.wallet_1_path(), cls.wallet_1_dest())
            cls._wallet1 = UserWallet.Open(UserWalletTestCase.wallet_1_dest(),
                                           to_aes_key(UserWalletTestCase.wallet_1_pass()))
        return cls._wallet1

    def test_send_neo(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            wallet = self.GetWallet1(recreate=True)
            args = ['neo', self.watch_addr_str, '50']

            framework = construct_send_basic(wallet, args)
            res = process_transaction(wallet, contract_tx=framework[0], scripthash_from=framework[1], fee=framework[2], owners=framework[3], user_tx_attributes=framework[4])

            self.assertTrue(res)

    def test_send_gas_mimic_prompt(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            wallet = self.GetWallet1(recreate=True)
            args = ['gas', self.watch_addr_str, '5']
            res = False

            framework = construct_send_basic(wallet, args)
            if type(framework) is list:
                res = process_transaction(wallet, contract_tx=framework[0], scripthash_from=framework[1], fee=framework[2], owners=framework[3], user_tx_attributes=framework[4])

            self.assertTrue(res)

    def test_send_with_fee_and_from_addr(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            wallet = self.GetWallet1(recreate=True)
            args = ['neo', self.watch_addr_str, '1', '--from-addr=AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3', '--fee=0.005']

            framework = construct_send_basic(wallet, args)
            res = process_transaction(wallet, contract_tx=framework[0], scripthash_from=framework[1], fee=framework[2], owners=framework[3], user_tx_attributes=framework[4])

            self.assertTrue(res)  # verify successful tx

            json_res = res.ToJson()
            self.assertEqual(self.watch_addr_str, json_res['vout'][0]['address'])  # verify correct address_to
            self.assertEqual(self.wallet_1_addr, json_res['vout'][1]['address'])  # verify correct address_from
            self.assertEqual(json_res['net_fee'], "0.005")  # verify correct fee

    def test_send_no_wallet(self):

        wallet = None
        args = ['neo', self.watch_addr_str, '50']

        framework = construct_send_basic(wallet, args)

        self.assertFalse(framework)

    def test_send_bad_args(self):

        wallet = self.GetWallet1(recreate=True)
        args = ['neo', self.watch_addr_str]  # too few args

        framework = construct_send_basic(wallet, args)

        self.assertFalse(framework)

    def test_send_bad_assetid(self):

        wallet = self.GetWallet1(recreate=True)
        args = ['blah', self.watch_addr_str, '12']

        framework = construct_send_basic(wallet, args)

        self.assertFalse(framework)

    def test_send_bad_address_to(self):

        wallet = self.GetWallet1(recreate=True)
        address_to = 'AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkE'  # address_to is too short causing ToScriptHash to fail
        args = ['neo', address_to, '12']

        framework = construct_send_basic(wallet, args)

        self.assertFalse(framework)

    def test_send_bad_address_from(self):

        wallet = self.GetWallet1(recreate=True)
        address_from = '--from-addr=AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc'  # address_from is too short causing ToScriptHash to fail
        args = ['neo', self.watch_addr_str, '12', address_from]

        framework = construct_send_basic(wallet, args)

        self.assertFalse(framework)

    def test_send_negative_amount(self):

        wallet = self.GetWallet1(recreate=True)
        args = ['neo', self.watch_addr_str, '-12']

        framework = construct_send_basic(wallet, args)

        self.assertFalse(framework)

    def test_send_zero_amount(self):

        wallet = self.GetWallet1(recreate=True)
        args = ['neo', self.watch_addr_str, '0']

        framework = construct_send_basic(wallet, args)

        self.assertFalse(framework)

    def test_send_weird_amount(self):

        wallet = self.GetWallet1(recreate=True)
        args = ['neo', self.watch_addr_str, '12.abc3']

        framework = construct_send_basic(wallet, args)

        self.assertFalse(framework)

    def test_send_bad_precision_amount(self):

        wallet = self.GetWallet1(recreate=True)
        args = ['neo', self.watch_addr_str, '12.01']

        framework = construct_send_basic(wallet, args)

        self.assertFalse(framework)

    def test_send_negative_fee(self):

        wallet = self.GetWallet1(recreate=True)
        args = ['neo', self.watch_addr_str, '12', '--fee=-0.005']

        framework = construct_send_basic(wallet, args)

        self.assertFalse(framework)

    def test_send_weird_fee(self):

        wallet = self.GetWallet1(recreate=True)
        args = ['neo', self.watch_addr_str, '12', '--fee=0.0abc']

        framework = construct_send_basic(wallet, args)

        self.assertFalse(framework)

    def test_send_token_bad(self):

        wallet = self.GetWallet1(recreate=True)

        token_hash = 'f8d448b227991cf07cb96a6f9c0322437f1599b9'
        ImportToken(wallet, token_hash)

        args = ['NEP5', self.watch_addr_str, '32']

        framework = construct_send_basic(wallet, args)

        self.assertFalse(framework)

    def test_send_token_ok(self):
        with patch('neo.Prompt.Commands.Tokens.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            wallet = self.GetWallet1(recreate=True)

            token_hash = '31730cc9a1844891a3bafd1aa929a4142860d8d3'
            ImportToken(wallet, token_hash)

            args = ['NXT4', self.watch_addr_str, '30', '--from-addr=%s' % self.wallet_1_addr]

            framework = construct_send_basic(wallet, args)

            self.assertTrue(framework)

    def test_insufficient_funds(self):

        wallet = self.GetWallet1(recreate=True)
        args = ['gas', self.watch_addr_str, '72620']

        framework = construct_send_basic(wallet, args)
        res = process_transaction(wallet, contract_tx=framework[0], scripthash_from=framework[1], fee=framework[2], owners=framework[3], user_tx_attributes=framework[4])

        self.assertFalse(res)

    def test_bad_password(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=['blah']):
            wallet = self.GetWallet1(recreate=True)
            args = ['neo', self.watch_addr_str, '50']

            framework = construct_send_basic(wallet, args)
            res = process_transaction(wallet, contract_tx=framework[0], scripthash_from=framework[1], fee=framework[2], owners=framework[3], user_tx_attributes=framework[4])

            self.assertFalse(res)

    @patch.object(Send, 'gather_signatures')
    def test_owners(self, mock):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            wallet = self.GetWallet1(recreate=True)

            args = ['gas', self.wallet_1_addr, '2', "--owners=['AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK','APRgMZHZubii29UXF9uFa6sohrsYupNAvx']"]

            framework = construct_send_basic(wallet, args)
            process_transaction(wallet, contract_tx=framework[0], scripthash_from=framework[1], fee=framework[2], owners=framework[3], user_tx_attributes=framework[4])

            self.assertTrue(mock.called)

    def test_attributes(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            wallet = self.GetWallet1(recreate=True)
            args = ['gas', self.watch_addr_str, '2', '--tx-attr={"usage":241,"data":"This is a remark"}']

            framework = construct_send_basic(wallet, args)
            res = process_transaction(wallet, contract_tx=framework[0], scripthash_from=framework[1], fee=framework[2], owners=framework[3], user_tx_attributes=framework[4])

            self.assertTrue(res)
            self.assertEqual(2, len(res.Attributes))  # By default the script_hash of the transaction sender is added to the TransactionAttribute list, therefore the Attributes length is `count` + 1

    def test_multiple_attributes(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            wallet = self.GetWallet1(recreate=True)
            args = ['gas', self.watch_addr_str, '2', '--tx-attr=[{"usage":241,"data":"This is a remark"},{"usage":242,"data":"This is a remark 2"}]']

            framework = construct_send_basic(wallet, args)
            res = process_transaction(wallet, contract_tx=framework[0], scripthash_from=framework[1], fee=framework[2], owners=framework[3], user_tx_attributes=framework[4])

            self.assertTrue(res)
            self.assertEqual(3, len(res.Attributes))

    def test_bad_attributes(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            wallet = self.GetWallet1(recreate=True)
            args = ['gas', self.watch_addr_str, '2', '--tx-attr=[{"usa:241"data":his is a remark"}]']

            framework = construct_send_basic(wallet, args)
            res = process_transaction(wallet, contract_tx=framework[0], scripthash_from=framework[1], fee=framework[2], owners=framework[3], user_tx_attributes=framework[4])

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
                wallet = self.GetWallet1(recreate=True)
                args = ['gas', self.watch_addr_str, '2']

                framework = construct_send_basic(wallet, args)
                res = process_transaction(wallet, contract_tx=framework[0], scripthash_from=framework[1], fee=framework[2], owners=framework[3], user_tx_attributes=framework[4])

                self.assertFalse(res)

    def test_fails_to_relay_tx(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
            with patch('neo.Prompt.Commands.Send.NodeLeader.Relay', return_value=False):
                wallet = self.GetWallet1(recreate=True)
                args = ['gas', self.watch_addr_str, '2']

                framework = construct_send_basic(wallet, args)
                res = process_transaction(wallet, contract_tx=framework[0], scripthash_from=framework[1], fee=framework[2], owners=framework[3], user_tx_attributes=framework[4])

                self.assertFalse(res)

    @patch('neo.Prompt.Commands.Send.traceback')
    def test_could_not_send(self, mocked_tracback_module):
        # mocking traceback module to avoid stacktrace printing during test run

        wallet = self.GetWallet1(recreate=True)
        args = ['gas', self.watch_addr_str, '2']

        contract_tx, scripthash_from, fee, owners, user_tx_attributes = construct_send_basic(wallet, args)
        scripthash_change = scripthash_from
        # mocking wallet to trigger the exception
        wallet = MagicMock()
        wallet.MakeTransaction.side_effect = Exception
        res = process_transaction(wallet, contract_tx, scripthash_from, scripthash_change, fee, owners, user_tx_attributes)  # forces the 'try:' to fail

        self.assertFalse(res)

    def test_sendmany_good_simple(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=["neo", self.watch_addr_str, "1", "gas", self.watch_addr_str, "1", UserWalletTestCase.wallet_1_pass()]):

            wallet = self.GetWallet1(recreate=True)
            args = ["2"]

            framework = construct_send_many(wallet, args)
            res = process_transaction(wallet, contract_tx=framework[0], scripthash_from=framework[1], scripthash_change=framework[2], fee=framework[3], owners=framework[4], user_tx_attributes=framework[5])

            self.assertTrue(res)  # verify successful tx

            json_res = res.ToJson()
            self.assertEqual(self.watch_addr_str, json_res['vout'][0]['address'])  # verify correct address_to

            # check for 2 transfers
            transfers = 0
            for info in json_res['vout']:
                if info['address'] == self.watch_addr_str:
                    transfers += 1
            self.assertEqual(2, transfers)

    def test_sendmany_good_complex(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=["neo", "AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK", "1", "gas", "AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK", "1", UserWalletTestCase.wallet_1_pass()]):
            wallet = self.GetWallet1(recreate=True)
            args = ["2", '--from-addr=%s' % self.wallet_1_addr, '--change-addr=%s' % self.watch_addr_str, '--fee=0.005']

            address_from_account_state = Blockchain.Default().GetAccountState(self.wallet_1_addr).ToJson()
            address_from_gas_bal = address_from_account_state['balances']['0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7']

            framework = construct_send_many(wallet, args)
            res = process_transaction(wallet, contract_tx=framework[0], scripthash_from=framework[1], scripthash_change=framework[2], fee=framework[3], owners=framework[4], user_tx_attributes=framework[5])

            self.assertTrue(res)  # verify successful tx

            json_res = res.ToJson()
            self.assertEqual("AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK", json_res['vout'][0]['address'])  # verify correct address_to
            self.assertEqual(self.watch_addr_str, json_res['vout'][2]['address'])  # verify correct change address
            self.assertEqual(float(address_from_gas_bal) - 1 - 0.005, float(json_res['vout'][3]['value']))
            self.assertEqual('0.005', json_res['net_fee'])

    def test_sendmany_no_wallet(self):

        wallet = None
        args = ['2']

        framework = construct_send_many(wallet, args)

        self.assertFalse(framework)

    def test_sendmany_bad_args(self):

        wallet = self.GetWallet1(recreate=True)
        args = []  # too few args

        framework = construct_send_many(wallet, args)

        self.assertFalse(framework)

    def test_sendmany_bad_outgoing(self):

        wallet = self.GetWallet1(recreate=True)
        args = ['0']  # too few outgoing

        framework = construct_send_many(wallet, args)

        self.assertFalse(framework)

    def test_sendmany_weird_outgoing(self):

        wallet = self.GetWallet1(recreate=True)
        args = ['0.5']  # weird number outgoing

        framework = construct_send_many(wallet, args)

        self.assertFalse(framework)

    def test_sendmany_bad_assetid(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=["neo", self.watch_addr_str, "1", "blah", self.watch_addr_str, "1"]):
            wallet = self.GetWallet1(recreate=True)
            args = ['2']

            framework = construct_send_many(wallet, args)

            self.assertFalse(framework)

    def test_sendmany_token(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=["neo", self.watch_addr_str, "1", "NXT4", self.watch_addr_str, "32"]):
            wallet = self.GetWallet1(recreate=True)

            token_hash = '31730cc9a1844891a3bafd1aa929a4142860d8d3'
            ImportToken(wallet, token_hash)

            args = ["2", '--from-addr=%s' % self.wallet_1_addr]

            framework = construct_send_many(wallet, args)

            self.assertFalse(framework)

    def test_sendmany_bad_address_to(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=["neo", self.watch_addr_str, "1", "gas", "AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkE", "1"]):  # address is too short

            wallet = self.GetWallet1(recreate=True)
            args = ['2']

            framework = construct_send_many(wallet, args)

            self.assertFalse(framework)

    def test_sendmany_negative_amount(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=["neo", self.watch_addr_str, "1", "gas", self.watch_addr_str, "-1"]):
            wallet = self.GetWallet1(recreate=True)
            args = ['2']

            framework = construct_send_many(wallet, args)

            self.assertFalse(framework)

    def test_sendmany_zero_amount(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=["neo", self.watch_addr_str, "1", "gas", self.watch_addr_str, "0"]):
            wallet = self.GetWallet1(recreate=True)
            args = ['2']

            framework = construct_send_many(wallet, args)

            self.assertFalse(framework)

    def test_sendmany_weird_amount(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=["neo", self.watch_addr_str, "1", "gas", self.watch_addr_str, "5.abc3"]):
            wallet = self.GetWallet1(recreate=True)
            args = ['2']

            framework = construct_send_many(wallet, args)

            self.assertFalse(framework)

    def test_sendmany_bad_precision_amount(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=["gas", self.watch_addr_str, "1", "neo", self.watch_addr_str, "5.01"]):
            wallet = self.GetWallet1(recreate=True)
            args = ['2']

            framework = construct_send_many(wallet, args)

            self.assertFalse(framework)

    def test_sendmany_bad_address_from(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=["neo", self.watch_addr_str, "1", "gas", self.watch_addr_str, "1"]):
            wallet = self.GetWallet1(recreate=True)
            address_from = '--from-addr=AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc'  # address_from is too short causing ToScriptHash to fail
            args = ['2', address_from]

            framework = construct_send_many(wallet, args)

            self.assertFalse(framework)

    def test_sendmany_bad_change_address(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=["neo", self.watch_addr_str, "1", "gas", self.watch_addr_str, "1"]):
            wallet = self.GetWallet1(recreate=True)
            change_address = '--change-addr=AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkE'  # change address is too short causing ToScriptHash to fail
            args = ['2', change_address]

            framework = construct_send_many(wallet, args)

            self.assertFalse(framework)

    def test_sendmany_negative_fee(self):
        with patch('neo.Prompt.Commands.Send.prompt', side_effect=["neo", self.watch_addr_str, "1", "gas", self.watch_addr_str, "1"]):
            wallet = self.GetWallet1(recreate=True)
            args = ['2', '--fee=-0.005']

            framework = construct_send_many(wallet, args)

            self.assertFalse(framework)
