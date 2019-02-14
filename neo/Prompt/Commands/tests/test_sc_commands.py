import os
import shutil
import warnings
from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Wallets.utils import to_aes_key
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neocore.UInt160 import UInt160
from neo.Prompt.Commands.SC import CommandSC
from neo.Prompt.PromptData import PromptData
from mock import patch
from io import StringIO
from boa.compiler import Compiler
from neo.Settings import settings


class CommandSCTestCase(WalletFixtureTestCase):
    wallet_1_script_hash = UInt160(data=b'\x1c\xc9\xc0\\\xef\xff\xe6\xcd\xd7\xb1\x82\x81j\x91R\xec!\x8d.\xc0')

    wallet_1_addr = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'

    import_watch_addr = UInt160(data=b'\x08t/\\P5\xac-\x0b\x1c\xb4\x94tIyBu\x7f1*')
    watch_addr_str = 'AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEm'
    _wallet1 = None
    _wallet3 = None

    @classmethod
    def GetWallet1(cls, recreate=False):
        if cls._wallet1 is None or recreate:
            shutil.copyfile(cls.wallet_1_path(), cls.wallet_1_dest())
            cls._wallet1 = UserWallet.Open(CommandSCTestCase.wallet_1_dest(),
                                           to_aes_key(CommandSCTestCase.wallet_1_pass()))
        return cls._wallet1

    @classmethod
    def GetWallet3(cls, recreate=False):

        if cls._wallet3 is None or recreate:
            shutil.copyfile(cls.wallet_3_path(), cls.wallet_3_dest())
            cls._wallet3 = UserWallet.Open(cls.wallet_3_dest(),
                                           to_aes_key(cls.wallet_3_pass()))

        return cls._wallet3

    @classmethod
    def tearDown(cls):
        PromptData.Wallet = None
        try:
            os.remove("neo/Prompt/Commands/tests/SampleSC.avm")
            os.remove("neo/Prompt/Commands/tests/SampleSC.debug.json")
        except FileNotFoundError:  # expected during test_sc
            pass

    def test_sc(self):
        # with no subcommand
        with patch('sys.stdout', new=StringIO()) as mock_print:
            res = CommandSC().execute(None)
            self.assertFalse(res)
            self.assertIn("run `sc help` to see supported queries", mock_print.getvalue())

        # with invalid command
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['badcommand']
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("badcommand is an invalid parameter", mock_print.getvalue())

    def test_sc_build(self):
        warnings.filterwarnings('ignore', category=ResourceWarning)  # filters warnings about unclosed files
        # test no input
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['build']
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("Please specify the required parameter", mock_print.getvalue())

        # test bad path
        args = ['build', 'SampleSC.py']
        res = CommandSC().execute(args)
        self.assertFalse(res)

        # test successful compilation
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['build', 'neo/Prompt/Commands/tests/SampleSC.py']
            res = CommandSC().execute(args)
            self.assertTrue(res)
            self.assertIn("Saved output to neo/Prompt/Commands/tests/SampleSC.avm", mock_print.getvalue())

    def test_sc_buildrun(self):
        warnings.filterwarnings('ignore', category=ResourceWarning)  # filters warnings about unclosed files
        # test no input
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['build_run']
            tx, result, total_ops, engine = CommandSC().execute(args)
            self.assertFalse(tx)
            self.assertIn("Please specify the required parameters", mock_print.getvalue())

        # test bad path
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['build_run', 'SampleSC.py', 'True', 'False', 'False', '070502', '02', '--i']
            tx, result, total_ops, engine = CommandSC().execute(args)
            self.assertEqual(tx, None)
            self.assertEqual(result, None)
            self.assertEqual(total_ops, None)
            self.assertEqual(engine, None)
            self.assertIn("Please check the path to your Python (.py) file to compile", mock_print.getvalue())

        # test no open wallet
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['build_run', 'neo/Prompt/Commands/tests/SampleSC.py', 'True', 'False', 'False', '070502', '02',
                    'add' 'AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy' '3']
            tx, result, total_ops, engine = CommandSC().execute(args)
            self.assertEqual(tx, None)
            self.assertEqual(result, None)
            self.assertEqual(total_ops, None)
            self.assertEqual(engine, None)
            self.assertIn("Please open a wallet to test build contract", mock_print.getvalue())

        # test bad args
        PromptData.Wallet = self.GetWallet1(recreate=True)
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['build_run', 'neo/Prompt/Commands/tests/SampleSC.py', 'True', 'False', '070502', '02', 'add', 'AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy',
                    '3']  # missing payable flag
            tx, result, total_ops, engine = CommandSC().execute(args)
            self.assertFalse(tx)
            self.assertIn("run `sc build_run help` to see supported queries", mock_print.getvalue())

        # test successful build and run
        PromptData.Wallet = self.GetWallet1(recreate=True)
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['build_run', 'neo/Prompt/Commands/tests/SampleSC.py', 'True', 'False', 'False', '070502', '02', 'add', 'AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy',
                    '3']
            tx, result, total_ops, engine = CommandSC().execute(args)
            self.assertTrue(tx)
            self.assertEqual(str(result[0]), '3')
            self.assertIn("Test deploy invoke successful", mock_print.getvalue())

        # test successful build and run with prompted input
        # PromptData.Wallet = self.GetWallet1(recreate=True)
        # with patch('sys.stdout', new=StringIO()) as mock_print:
        #     with patch('neo.Prompt.Utils.PromptSession.prompt', side_effect=['remove', 'AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy', '3']):
        #         args = ['build_run', 'neo/Prompt/Commands/tests/SampleSC.py', 'True', 'False', 'False', '070502', '02', '--i']
        #         tx, result, total_ops, engine = CommandSC().execute(args)
        #         self.assertTrue(tx)
        #         self.assertEqual(str(result[0]), '0')
        #         self.assertIn("Test deploy invoke successful", mock_print.getvalue())

        # test invoke failure (SampleSC requires three inputs)
        PromptData.Wallet = self.GetWallet1(recreate=True)
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['build_run', 'neo/Prompt/Commands/tests/SampleSC.py', 'True', 'False', 'False', '0705', '02', 'balance',
                    'AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy']
            tx, result, total_ops, engine = CommandSC().execute(args)
            self.assertIsNone(tx)
            self.assertIn("Test invoke failed", mock_print.getvalue())

    def test_sc_loadrun(self):
        warnings.filterwarnings('ignore', category=ResourceWarning)  # filters warnings about unclosed files
        # test no input
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['load_run']
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("Please specify the required parameters", mock_print.getvalue())

        # test bad path
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['load_run', 'neo/Prompt/Commands/tests/SampleSC.py', 'True', 'False', 'False', '070502', '02', '--i']
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("run `sc load_run help` to see supported queries", mock_print.getvalue())

        # build the .avm file
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['build', 'neo/Prompt/Commands/tests/SampleSC.py']
            res = CommandSC().execute(args)
            self.assertTrue(res)
            self.assertIn("Saved output to neo/Prompt/Commands/tests/SampleSC.avm", mock_print.getvalue())

        # test no open wallet
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['load_run', 'neo/Prompt/Commands/tests/SampleSC.avm', 'True', 'False', 'False', '070502', '02',
                    'add' 'AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy' '3']
            tx, result, total_ops, engine = CommandSC().execute(args)
            self.assertEqual(tx, None)
            self.assertEqual(result, None)
            self.assertEqual(total_ops, None)
            self.assertEqual(engine, None)
            self.assertIn("Please open a wallet to test build contract", mock_print.getvalue())

        # test bad args
        PromptData.Wallet = self.GetWallet1(recreate=True)
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['load_run', 'neo/Prompt/Commands/tests/SampleSC.avm', 'True', 'False', '070502', '02', 'balance', 'AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy',
                    '0']  # missing payable flag
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("run `sc load_run help` to see supported queries", mock_print.getvalue())

        # test successful load and run with from-addr
        PromptData.Wallet = self.GetWallet1(recreate=True)
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['load_run', 'neo/Prompt/Commands/tests/SampleSC.avm', 'True', 'False', 'False', '070502', '02', 'balance',
                    'AG4GfwjnvydAZodm4xEDivguCtjCFzLcJy', '0', '--from-addr=' + self.wallet_1_addr]
            tx, result, total_ops, engine = CommandSC().execute(args)
            self.assertTrue(tx)
            self.assertIn("Test deploy invoke successful", mock_print.getvalue())

    def test_sc_deploy(self):
        # test no wallet
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['deploy']
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("Please open a wallet", mock_print.getvalue())

        PromptData.Wallet = self.GetWallet1(recreate=True)

        # test no input
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['deploy']
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("Please specify the required parameters", mock_print.getvalue())

        # test bad path (.py instead of .avm)
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['deploy', 'neo/Prompt/Commands/tests/SampleSC.py', 'False', 'False', 'False', '070502', '02']
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("Please load a compiled .avm file", mock_print.getvalue())

        # test with invalid boolean option(s) for contract
        path_dir = 'neo/Prompt/Commands/tests/'
        Compiler.instance().load_and_save(path_dir + 'SampleSC.py', use_nep8=False)
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['deploy', path_dir + 'SampleSC.avm', 'Blah', 'False', 'False', '070502', '02']
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("Invalid boolean option", mock_print.getvalue())

        # test with invalid input parameter type (void)
        path_dir = 'neo/Prompt/Commands/tests/'
        Compiler.instance().load_and_save(path_dir + 'SampleSC.py', use_nep8=False)
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['deploy', path_dir + 'SampleSC.avm', 'True', 'False', 'False', '0705ff', '02']
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("Void is not a valid input parameter type", mock_print.getvalue())

        # with failing to gather contract details
        path_dir = 'neo/Prompt/Commands/tests/'
        Compiler.instance().load_and_save(path_dir + 'SampleSC.py', use_nep8=False)
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.SC.GatherContractDetails', side_effect=[(None)]):
                args = ['deploy', path_dir + 'SampleSC.avm', 'True', 'False', 'False', '070502', '02']
                res = CommandSC().execute(args)
                self.assertFalse(res)
                self.assertIn("Failed to generate deploy script", mock_print.getvalue())

        # test ok contract parameter gathering, but bad passw
        path_dir = 'neo/Prompt/Commands/tests/'
        Compiler.instance().load_and_save(path_dir + 'SampleSC.py', use_nep8=False)

        prompt_entries = ['test_name', 'test_version', 'test_author', 'test_email', 'test_description', 'False', 'False', 'False', 'bad_pw']
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.LoadSmartContract.prompt', side_effect=prompt_entries):
                with patch('neo.Prompt.Commands.SC.prompt', side_effect=['bad_passw']):
                    args = ['deploy', path_dir + 'SampleSC.avm', 'True', 'False', 'False', '070502', '02']
                    res = CommandSC().execute(args)
                    self.assertFalse(res)
                    self.assertTrue(mock_print.getvalue().endswith('Incorrect password\n'))

        # test ok contract parameter gathering, but test_invoke failure
        path_dir = 'neo/Prompt/Commands/tests/'
        Compiler.instance().load_and_save(path_dir + 'SampleSC.py', use_nep8=False)

        prompt_entries = ['test_name', 'test_version', 'test_author', 'test_email', 'test_description', 'False', 'False', 'False', 'bad_pw']
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.LoadSmartContract.prompt', side_effect=prompt_entries):
                with patch('neo.Prompt.Commands.SC.test_invoke', side_effect=[(None, None, None, None, None)]):
                    args = ['deploy', path_dir + 'SampleSC.avm', 'True', 'False', 'False', '070502', '02']
                    res = CommandSC().execute(args)
                    self.assertFalse(res)
                    self.assertIn("Test invoke failed", mock_print.getvalue())

        # test with ok contract parameter gathering, but bad fee
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.LoadSmartContract.prompt', side_effect=prompt_entries):
                with patch('neo.Prompt.Commands.SC.prompt', side_effect=[self.wallet_1_pass()]):
                    args = ['deploy', path_dir + 'SampleSC.avm', 'True', 'False', 'False', '070502', '02', '--fee=0.001!']
                    res = CommandSC().execute(args)
                    self.assertFalse(res)
                    self.assertIn("invalid amount format", mock_print.getvalue())

        # test with ok contract parameter gathering, but negative fee
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.LoadSmartContract.prompt', side_effect=prompt_entries):
                with patch('neo.Prompt.Commands.SC.prompt', side_effect=[self.wallet_1_pass()]):
                    args = ['deploy', path_dir + 'SampleSC.avm', 'True', 'False', 'False', '070502', '02', '--fee=-0.001']
                    res = CommandSC().execute(args)
                    self.assertFalse(res)
                    self.assertIn("invalid amount format", mock_print.getvalue())

        # test with ok contract parameter gathering, ok passw, and priority fee (just insufficient funds to deploy)
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.LoadSmartContract.prompt', side_effect=prompt_entries):
                with patch('neo.Prompt.Commands.SC.prompt', side_effect=[self.wallet_1_pass()]):
                    args = ['deploy', path_dir + 'SampleSC.avm', 'True', 'False', 'False', '070502', '02', '--fee=0.001']
                    res = CommandSC().execute(args)
                    self.assertFalse(res)
                    self.assertIn("Priority Fee (0.001) + Deploy Invoke TX Fee (0.0) = 0.001", mock_print.getvalue())
                    self.assertTrue(mock_print.getvalue().endswith('Insufficient funds\n'))

        # test with ok contract parameter gathering, and tx is too large for low priority (e.g. >1024), just insufficient funds to deploy
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.LoadSmartContract.prompt', side_effect=prompt_entries):
                with patch('neo.Prompt.Commands.SC.prompt', side_effect=[self.wallet_1_pass()]):
                    with patch('neo.Core.TX.InvocationTransaction.InvocationTransaction.Size', return_value=1026):  # returns a size of 1026
                        args = ['deploy', path_dir + 'SampleSC.avm', 'True', 'False', 'False', '070502', '02']
                        res = CommandSC().execute(args)
                        self.assertFalse(res)
                        self.assertIn("Deploy Invoke TX Fee: 0.001", mock_print.getvalue())  # notice the required fee is equal to the low priority threshold
                        self.assertTrue(mock_print.getvalue().endswith('Insufficient funds\n'))

        # test with ok contract parameter gathering, but tx size exceeds the size covered by the high priority fee (e.g. >1124), just insufficient funds to deploy
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.LoadSmartContract.prompt', side_effect=prompt_entries):
                with patch('neo.Prompt.Commands.SC.prompt', side_effect=[self.wallet_1_pass()]):
                    with patch('neo.Core.TX.InvocationTransaction.InvocationTransaction.Size', return_value=1411):  # returns a size of 1411
                        args = ['deploy', path_dir + 'SampleSC.avm', 'True', 'False', 'False', '070502', '02']
                        res = CommandSC().execute(args)
                        self.assertFalse(res)
                        self.assertIn("Deploy Invoke TX Fee: 0.00387", mock_print.getvalue())  # notice the required fee is now greater than the low priority threshold
                        self.assertTrue(mock_print.getvalue().endswith('Insufficient funds\n'))

    def test_sc_invoke(self):
        token_hash_str = '31730cc9a1844891a3bafd1aa929a4142860d8d3'

        # test no open wallet
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['invoke', token_hash_str, 'symbol', '[]']
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("Please open a wallet", mock_print.getvalue())

        PromptData.Wallet = self.GetWallet3(recreate=True)

        # test invalid contract script hash
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['invoke', 'invalid_hash', 'invalid_params']
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("Invalid script hash", mock_print.getvalue())

        # test invalid parameter count (missing required `contract`)
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['invoke', '--from-addr=bla']
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("Please specify the required parameters", mock_print.getvalue())

        # test with an script_hash that cannot be found
        with patch('sys.stdout', new=StringIO()) as mock_print:
            bad_contract = 'a' * 40  # passes basic script_hash length check, but won't find actual contract
            args = ['invoke', bad_contract, 'name', '[]']
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("Error testing contract invoke", mock_print.getvalue())

        # test with negative fee
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.SC.prompt', side_effect=[self.wallet_3_pass()]):
                args = ['invoke', token_hash_str, 'symbol', '[]', '--fee=-0.001']
                res = CommandSC().execute(args)
                self.assertFalse(res)
                self.assertIn("invalid amount format", mock_print.getvalue())

        # test with weird fee
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.SC.prompt', side_effect=[self.wallet_3_pass()]):
                args = ['invoke', token_hash_str, 'symbol', '[]', '--fee=0.0abc']
                res = CommandSC().execute(args)
                self.assertFalse(res)
                self.assertIn("invalid amount format", mock_print.getvalue())

        # test ok, but bad passw to send to network
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.SC.prompt', side_effect=["blah"]):
                args = ['invoke', token_hash_str, 'symbol', '[]']
                res = CommandSC().execute(args)
                self.assertFalse(res)
                self.assertIn("Incorrect password", mock_print.getvalue())

        # test ok
        with patch('sys.stdout', new=StringIO()) as mock_print:
            with patch('neo.Prompt.Commands.SC.prompt', side_effect=[self.wallet_3_pass()]):
                args = ['invoke', token_hash_str, 'symbol', '[]', '--fee=0.001']
                res = CommandSC().execute(args)
                # not the best check, but will do for now
                self.assertTrue(res)
                self.assertIn("Priority Fee (0.001) + Invoke TX Fee (0.0001) = 0.0011", mock_print.getvalue())

    def test_sc_debugstorage(self):
        # test with insufficient parameters
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['debugstorage']
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("Please specify the required parameter", mock_print.getvalue())

        # test with bad parameter
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['debugstorage', 'blah']
            res = CommandSC().execute(args)
            self.assertFalse(res)
            self.assertIn("Invalid option", mock_print.getvalue())

        # test with reset parameter
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['debugstorage', 'reset']
            res = CommandSC().execute(args)
            self.assertTrue(res)
            self.assertIn("Reset debug storage", mock_print.getvalue())

        # test turning on
        args = ['debugstorage', 'on']
        res = CommandSC().execute(args)
        self.assertTrue(res)
        self.assertTrue(settings.USE_DEBUG_STORAGE)

        # test turning off
        args = ['debugstorage', 'off']
        res = CommandSC().execute(args)
        self.assertTrue(res)
        self.assertFalse(settings.USE_DEBUG_STORAGE)
