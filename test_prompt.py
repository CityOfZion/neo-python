import io
import os
from prompt import PromptInterface
from neo.Utils.NeoTestCase import NeoTestCase
from mock import patch, PropertyMock


class PromptTestCase(NeoTestCase):

    def setUp(self):
        self.cli = PromptInterface()
        self.args = ['wallet', 'Wallets/testwallet']

    def tearDown(self):
        path = self.args[1]
        if os.path.isfile(path):
            os.remove(path)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_create_wallet_insufficient_parameters(self, mocked_stdout):
        """ Should warn the user that path to the wallet is missing """
        args = ['wallet']
        self.cli.do_create(args)
        self.assertEqual("Please specify a path\n", mocked_stdout.getvalue())

    @patch('prompt.Blockchain.Height', new_callable=PropertyMock)
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('prompt.prompt')
    def test_create_wallet(self, mocked_prompt, mocked_stdout, mocked_blockchain_height):
        """ Should successfully create a wallet"""
        # default return value for password entry prompt
        mocked_prompt.return_value = '1234567890'
        mocked_blockchain_height.return_value = 0
        self.cli.do_create(self.args)

        expect_wallet_print1 = '"path": "{}",'.format(self.args[1])
        expect_wallet_print2 = '"percent_synced": 0'

        self.assertTrue(os.path.isfile(self.args[1]))
        self.assertIn(expect_wallet_print1, mocked_stdout.getvalue())
        self.assertIn(expect_wallet_print2, mocked_stdout.getvalue())

    @patch('prompt.os.path.exists')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_create_wallet_already_exists(self, mocked_stdout, mocked_os_path_exists):
        mocked_os_path_exists.return_value = True
        self.cli.do_create(self.args)
        self.assertEqual("File already exists\n", mocked_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('prompt.prompt')
    def test_create_wallet_password_miss_match(self, mocked_prompt, mocked_stdout):
        """ Should only accept equal passwords with a minimum length of 10 characters"""
        mocked_prompt.side_effect = ['pw_entry_1', 'pw_entry_2']
        self.cli.do_create(self.args)

        expected_msg = "please provide matching passwords that are at least 10 characters long\n"
        self.assertEqual(expected_msg, mocked_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('prompt.prompt')
    def test_create_wallet_password_too_short(self, mocked_prompt, mocked_stdout):
        """ Should only accept equal passwords with a minimum length of 10 characters"""
        mocked_prompt.side_effect = ['pw_entry1', 'pw_entry1']
        self.cli.do_create(self.args)

        expected_msg = "please provide matching passwords that are at least 10 characters long\n"
        self.assertEqual(expected_msg, mocked_stdout.getvalue())


    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('prompt.UserWallet.GetDefaultContract')
    @patch('prompt.prompt')
    def test_create_wallet_fail_to_get_default_contract(self, mocked_prompt, mocked_get_default_contract, mocked_stdout):
        """ Should notify the user that a default contract could not be found and that we're aborting wallet creation"""
        mocked_prompt.return_value = '1234567890'
        mocked_get_default_contract.side_effect = Exception("TEST EXCEPTION")
        self.cli.do_create(self.args)
        expected_error_msg = "Exception creating wallet"
        self.assertIn(expected_error_msg, mocked_stdout.getvalue())


    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('prompt.os.remove')
    @patch('prompt.UserWallet.GetDefaultContract')
    @patch('prompt.prompt')
    def test_create_wallet_fail_to_remove_wallet_on_exception(self, mocked_prompt, mocked_get_default_contract, mocked_remove, mocked_stdout):
        """ Should notify the user that the file could not be removed due to an OSError"""
        mocked_prompt.return_value = '1234567890'
        mocked_get_default_contract.side_effect = Exception("TEST EXCEPTION")
        mocked_remove.side_effect = OSError()
        self.cli.do_create(self.args)
        expected_error_msg = "Could not remove {}".format(self.args[1])
        self.assertIn(expected_error_msg, mocked_stdout.getvalue())
