from unittest import TestCase, skip
from neo.bin.tests.neo_cli_plugin_example.example_cmd import ExampleCmd
from neo.bin.tests.neo_cli_plugin_example.example_cmd2 import ExampleCmd2
from neo.bin.prompt import get_cli_commands
from mock import patch
from io import StringIO
import pexpect


class PromptTest(TestCase):

    @skip("Unreliable due to system resource dependency. Replace later with better alternative")
    def test_prompt_run(self):
        child = pexpect.spawn('python neo/bin/prompt.py')
        child.expect([pexpect.EOF, pexpect.TIMEOUT], timeout=10)  # if test is failing consider increasing timeout time
        before = child.before
        text = before.decode('utf-8', 'ignore')
        checktext = "neo>"
        self.assertIn(checktext, text)
        child.terminate()

    @skip("Unreliable due to system resource dependency. Replace later with better alternative")
    def test_prompt_open_wallet(self):
        child = pexpect.spawn('python neo/bin/prompt.py')
        child.send('open wallet fixtures/testwallet.db3\n')
        child.send('testpassword\n')
        child.expect([pexpect.EOF, pexpect.TIMEOUT], timeout=15)  # if test is failing consider increasing timeout time
        before = child.before
        text = before.decode('utf-8', 'ignore')
        checktext = "Opened"
        self.assertIn(checktext, text)
        child.terminate()

    def test_loading_cmd_directly(self):
        """Test that we can discover and load a Command in a module"""
        path = 'neo.bin.tests.neo_cli_plugin_example.example_cmd'
        res = get_cli_commands([path])
        self.assertIsInstance(res[0], ExampleCmd)

    def test_loading_cmds_from_folder(self):
        """
            Test that we can search through a folder of CMDs
            And only load CMDs that have _isGroupBaseCommand set to True
            Thus we should skip 'bad_example_cmd.py'

        """
        path = 'neo.bin.tests.neo_cli_plugin_example.*'
        res = get_cli_commands([path])
        self.assertEqual(len(res), 2)
        self.assertIsInstance(res[0], ExampleCmd)
        self.assertIsInstance(res[1], ExampleCmd2)

    def test_loading_invalid_cmd_directly(self):
        """Test that we can handle bad lookups due to user entry errors"""
        bad_package = 'neo_bad_package.bin.tests.neo_cli_plugin_example.example_cmd'

        with patch('sys.stdout', new=StringIO()) as mock_print:
            res = get_cli_commands([bad_package])
            self.assertEqual(len(res), 0)
            self.assertIn("Could not load CLI command package", mock_print.getvalue())

        bad_module_path = 'neo.bin.tests.neo_cli_plugin_example.non_existing_module'
        with patch('sys.stdout', new=StringIO()) as mock_print:
            res = get_cli_commands([bad_module_path])
            self.assertEqual(len(res), 0)
            self.assertIn("Could not load CLI command module", mock_print.getvalue())
