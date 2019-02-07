from neo.Prompt.Commands.tests.test_wallet_commands import UserWalletTestCaseBase
from io import StringIO
from neo.SmartContract.Contract import Contract
from mock import patch
from neo.Wallets.NEP5Token import NEP5Token
from neo.Prompt.Commands.Wallet import CommandWallet
from neo.Prompt.PromptData import PromptData
from neocore.UInt160 import UInt160


class UserWalletTestCase(UserWalletTestCaseBase):
    def test_wallet_import_baseclass(self):
        self.OpenWallet1()

        # test with no argument
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("run `import help` to see supported queries", mock_print.getvalue())

        # test with an invalid action
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'bad_action']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("is an invalid parameter", mock_print.getvalue())

        # test with a good action
        with patch('neo.Prompt.Commands.WalletImport.CommandWalletImport.execute_sub_command', side_effect=[True]):
            args = ['import', 'mocked_action']
            res = CommandWallet().execute(args)
            self.assertTrue(res)

    def test_wallet_import_wif(self):
        self.OpenWallet1()

        # test missing wif key argument
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'wif']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("specify the required parameter", mock_print.getvalue())

        # test with bad wif length
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'wif', 'too_short']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Please provide a wif with a length of 52 bytes", mock_print.getvalue())

        # test with invalid wif
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'wif', 'a' * 52]
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Invalid format", mock_print.getvalue())

        # test with exception in key creation
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.Wallet.PromptData.Wallet.CreateKey', side_effect=[Exception("unittest_error")]):
                with self.assertRaises(Exception) as context:
                    args = ['import', 'wif', 'Ky94Rq8rb1z8UzTthYmy1ApbZa9xsKTvQCiuGUZJZbaDJZdkvLRV']
                    res = CommandWallet().execute(args)
                    self.assertFalse(res)
                    self.assertIn("unittest_error", str(context.exception))
                    self.assertIn("unittest_error", mock_print.getvalue())

        # test with valid wif
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'wif', 'Ky94Rq8rb1z8UzTthYmy1ApbZa9xsKTvQCiuGUZJZbaDJZdkvLRV']
            res = CommandWallet().execute(args)
            self.assertTrue(res)
            self.assertIn(self.wallet_1_addr, mock_print.getvalue())

    def test_wallet_import_nep2(self):
        self.OpenWallet1()

        # test missing nep2 key argument
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'nep2']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("specify the required parameter", mock_print.getvalue())

        # test with bad nep2 length
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.WalletImport.prompt', side_effect=['random_passw']):
                args = ['import', 'nep2', 'too_short_nep2_key']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("Please provide a nep2_key with a length of 58 bytes", mock_print.getvalue())

        # test with ok NEP2, bad password
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.WalletImport.prompt', side_effect=['wrong_password']):
                args = ['import', 'nep2', '6PYK1E3skTFLgtsnVNKDCEdUQxeKbRmKBnbkPFxvGGggfeB2JacnMpqkcH']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("Wrong passphrase", mock_print.getvalue())

        # test with exception in key creation
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.WalletImport.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
                with patch('neo.Prompt.Commands.Wallet.PromptData.Wallet.CreateKey', side_effect=[Exception("unittest_error")]):
                    args = ['import', 'nep2', '6PYK1E3skTFLgtsnVNKDCEdUQxeKbRmKBnbkPFxvGGggfeB2JacnMpqkcH']
                    res = CommandWallet().execute(args)
                    self.assertFalse(res)
                    self.assertIn("Key creation error", mock_print.getvalue())
                    self.assertIn("unittest_error", mock_print.getvalue())

        # test with ok
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.WalletImport.prompt', side_effect=[UserWalletTestCase.wallet_1_pass()]):
                args = ['import', 'nep2', '6PYK1E3skTFLgtsnVNKDCEdUQxeKbRmKBnbkPFxvGGggfeB2JacnMpqkcH']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                # if we imported successfully we get the wallet1 address
                self.assertIn(self.wallet_1_addr, mock_print.getvalue())

    def test_wallet_import_watchaddr(self):
        self.OpenWallet1()

        # test missing wif key argument
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'watch_addr']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("specify the required parameter", mock_print.getvalue())

        # test with bad address
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'watch_addr', 'too_short_addr']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Invalid address specified", mock_print.getvalue())

        # test with good address
        with patch('sys.stdout', new=StringIO()) as mock_print:
            address = 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg'
            args = ['import', 'watch_addr', address]
            res = CommandWallet().execute(args)
            self.assertTrue(res)
            self.assertIn("Added address", mock_print.getvalue())
            self.assertIn("watch-only", mock_print.getvalue())
            self.assertIn(PromptData.Wallet.ToScriptHash(address), PromptData.Wallet.LoadWatchOnly())

        # test address already exists
        with patch('sys.stdout', new=StringIO()) as mock_print:
            address = 'AZfFBeBqtJvaTK9JqG8uk6N7FppQY6byEg'
            args = ['import', 'watch_addr', address]
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Address already exists in wallet", mock_print.getvalue())

    def test_wallet_import_multisig_address(self):
        self.OpenWallet1()

        # test missing all arguments
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'multisig_addr']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Please specify the minimum required parameters", mock_print.getvalue())

        # test invalid public key format
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'multisig_addr', 'not_a_public_key', 'arg2', 'arg3']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Invalid public key format", mock_print.getvalue())

        # test invalid public key format 2 (fail to convert to UIn160)
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'multisig_addr', 'Å' * 66, 'arg2', 'arg3']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Invalid public key format", mock_print.getvalue())

        # test with a public key not present in our own wallet
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'multisig_addr', '031a6c6fbbdf02ca351745fa86b9ba5a9452d785ac4f7fc2b7548ca2a46c4fcf4a', 'arg2', 'arg3']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Supplied first public key does not exist in own wallet", mock_print.getvalue())

        # test with bad minimum signature value 1
        with patch('sys.stdout', new=StringIO()) as mock_print:
            # 0 not allowed
            args = ['import', 'multisig_addr', '03cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6', '0', 'arg3']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Minimum signatures count cannot be lower than 1", mock_print.getvalue())

        # test with bad minimum signature value 2
        with patch('sys.stdout', new=StringIO()) as mock_print:
            # 'bla' is not a valid int
            args = ['import', 'multisig_addr', '03cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6', 'bla', 'arg3']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Invalid minimum signature count value", mock_print.getvalue())

        # test with insufficient remaining signing keys
        with patch('sys.stdout', new=StringIO()) as mock_print:
            # 0 not allowed
            args = ['import', 'multisig_addr', '03cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6', '3', 'key1']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Minimum required: 3 given: 2", mock_print.getvalue())

        # test with bad remaining signing key 1
        with patch('sys.stdout', new=StringIO()) as mock_print:
            # 0 not allowed
            args = ['import', 'multisig_addr', '03cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6', '1', 'too_short_signing_key']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Invalid signing key", mock_print.getvalue())

        # test with non unique signing keys
        with patch('sys.stdout', new=StringIO()) as mock_print:
            # 0 not allowed
            args = ['import', 'multisig_addr', '03cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6', '1',
                    '03cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Provided signing keys are not unique", mock_print.getvalue())

        # test with all good \o/
        with patch('sys.stdout', new=StringIO()) as mock_print:
            # 0 not allowed
            args = ['import', 'multisig_addr', '03cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6', '1',
                    '031a6c6fbbdf02ca351745fa86b9ba5a9452d785ac4f7fc2b7548ca2a46c4fcf4a']
            res = CommandWallet().execute(args)
            self.assertTrue(res)
            self.assertIn("Added multi-sig contract address", mock_print.getvalue())

    def test_wallet_import_token(self):
        token_hash = '31730cc9a1844891a3bafd1aa929a4142860d8d3'

        self.OpenWallet1()

        # test missing contract hash
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'token']
            res = CommandWallet().execute(args)
            self.assertIsNone(res)
            self.assertIn("specify the required parameter", mock_print.getvalue())

        # test with invalid contract hash
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'token', 'does_not_exist']
            res = CommandWallet().execute(args)
            self.assertIsNone(res)
            self.assertIn("Invalid contract hash", mock_print.getvalue())

        # test with valid but unknown contract hash
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'token', '31730cc9a1844891a3bafd1aa929a41000000000']
            res = CommandWallet().execute(args)
            self.assertIsNone(res)
            self.assertIn("Could not find the contract hash", mock_print.getvalue())

        # Test with impossibility to import the token
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Wallets.NEP5Token.NEP5Token.Query', side_effect=[None]):
                args = ['import', 'token', token_hash]
                res = CommandWallet().execute(args)
                self.assertIsNone(res)
                self.assertIn("Could not import token", mock_print.getvalue())

        # test with good hash
        args = ['import', 'token', token_hash]
        token = CommandWallet().execute(args)
        self.assertIsInstance(token, NEP5Token)
        self.assertEqual(token.name, 'NEX Template V4')
        self.assertEqual(token.symbol, 'NXT4')
        self.assertEqual(token.decimals, 8)
        self.assertEqual(token.Address, 'Ab61S1rk2VtCVd3NtGNphmBckWk4cfBdmB')

    def test_wallet_import_contract_addr(self):
        # test with no wallet open
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'contract_addr', 'contract_hash', 'pubkey']
            res = CommandWallet().execute(args)
            self.assertIsNone(res)
            self.assertIn("open a wallet", mock_print.getvalue())

        self.OpenWallet1()

        # test with not enough arguments (must have 2 arguments)
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'contract_addr']
            res = CommandWallet().execute(args)
            self.assertIsNone(res)
            self.assertIn("specify the required parameters", mock_print.getvalue())

        # test with too many arguments (must have 2 arguments)
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'contract_addr', 'arg1', 'arg2', 'arg3']
            res = CommandWallet().execute(args)
            self.assertIsNone(res)
            self.assertIn("specify the required parameters", mock_print.getvalue())

        # test with invalid contract hash
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'contract_addr', 'invalid_contract_hash', '03cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6']
            res = CommandWallet().execute(args)
            self.assertIsNone(res)
            self.assertIn("Invalid contract hash", mock_print.getvalue())

        # test with valid contract hash but that doesn't exist
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'contract_addr', '31730cc9a1844891a3bafd1aa929000000000000', '03cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6']
            res = CommandWallet().execute(args)
            self.assertIsNone(res)
            self.assertIn("Could not find contract", mock_print.getvalue())

        # test with invalid pubkey
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['import', 'contract_addr', '31730cc9a1844891a3bafd1aa929a4142860d8d3', 'invalid_pubkey']
            res = CommandWallet().execute(args)
            self.assertIsNone(res)
            self.assertIn("Invalid pubkey", mock_print.getvalue())

        # test with valid arguments
        contract_hash = UInt160.ParseString('31730cc9a1844891a3bafd1aa929a4142860d8d3')

        with patch('sys.stdout', new=StringIO()) as mock_print:
            self.assertIsNone(PromptData.Wallet.GetContract(contract_hash))

            args = ['import', 'contract_addr', '31730cc9a1844891a3bafd1aa929a4142860d8d3', '03cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6']
            res = CommandWallet().execute(args)
            self.assertIsInstance(res, Contract)
            self.assertTrue(PromptData.Wallet.GetContract(contract_hash))
            self.assertIn("Added contract address", mock_print.getvalue())
