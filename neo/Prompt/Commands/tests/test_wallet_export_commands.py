from neo.Prompt.Commands.tests.test_wallet_commands import UserWalletTestCaseBase
from mock import patch
from io import StringIO
from neo.Prompt.Commands.Wallet import CommandWallet


class UserWalletTestCase(UserWalletTestCaseBase):
    def test_wallet_export_baseclass(self):
        self.OpenWallet1()

        # test with no argument
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['export']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("run `export help` to see supported queries", mock_print.getvalue())

        # test with an invalid action
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['export', 'bad_action']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("is an invalid parameter", mock_print.getvalue())

        # test with a good action
        with patch('neo.Prompt.Commands.Wallet.CommandWalletExport.execute_sub_command', side_effect=[True]):
            args = ['export', 'mocked_action']
            res = CommandWallet().execute(args)
            self.assertTrue(res)

    def test_wallet_export_wif(self):
        self.OpenWallet1()
        # test missing address argument
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['export', 'wif']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("specify the required parameter", mock_print.getvalue())

        # test with an address that's not part of the wallet
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['export', 'wif', 'bad_address']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("Could not find address", mock_print.getvalue())

        # test with good address but bad passw
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.WalletExport.prompt', side_effect=['random_passw']):
                args = ['export', 'wif', self.wallet_1_addr]
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("Incorrect password", mock_print.getvalue())

        # test with good address
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.WalletExport.prompt', side_effect=[self.wallet_1_pass()]):
                args = ['export', 'wif', self.wallet_1_addr]
                res = CommandWallet().execute(args)
                self.assertTrue(res)
                self.assertIn("Ky94Rq8rb1z8UzTthYmy1ApbZa9xsKTvQCiuGUZJZbaDJZdkvLRV", mock_print.getvalue())

    def test_wallet_export_nep2(self):
        self.OpenWallet1()
        # test missing address argument
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['export', 'nep2']
            res = CommandWallet().execute(args)
            self.assertFalse(res)
            self.assertIn("specify the required parameter", mock_print.getvalue())

        # test with non matching passwords
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.WalletExport.prompt', side_effect=['random_passw', 'random_wrong_second_passw']):
                args = ['export', 'nep2', 'bad_address']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("Please provide matching passwords", mock_print.getvalue())

        # test with an address that's not part of the wallet
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.WalletExport.prompt', side_effect=['random_passw', 'random_passw']):
                args = ['export', 'nep2', 'bad_address']
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("Could not find address", mock_print.getvalue())

        # test with good address and but too short passphrase
        with patch('sys.stdout', new=StringIO()) as mock_print:
            pw_too_short = 'too_short'
            with patch('neo.Prompt.Commands.WalletExport.prompt', side_effect=[pw_too_short, pw_too_short, self.wallet_1_pass()]):
                args = ['export', 'nep2', self.wallet_1_addr]
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("Passphrase is too short", mock_print.getvalue())

        # test with good address but incorrect wallet password
        pw = UserWalletTestCase.wallet_1_pass()
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.WalletExport.prompt', side_effect=[pw, pw, 'incorrect_wallet_pw']):
                args = ['export', 'nep2', self.wallet_1_addr]
                res = CommandWallet().execute(args)
                self.assertFalse(res)
                self.assertIn("Incorrect password", mock_print.getvalue())

        # test with good address and good passphrase len
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.WalletExport.prompt', side_effect=[pw, pw, self.wallet_1_pass()]):
                args = ['export', 'nep2', self.wallet_1_addr]
                res = CommandWallet().execute(args)
                self.assertTrue(res)
                self.assertIn("6PYK1E3skTFLgtsnVNKDCEdUQxeKbRmKBnbkPFxvGGggfeB2JacnMpqkcH", mock_print.getvalue())
