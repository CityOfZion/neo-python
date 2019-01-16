import os
from neo.Settings import settings
from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.Prompt.Commands.Search import CommandSearch
from mock import patch
from io import StringIO


class CommandShowTestCase(BlockchainFixtureTestCase):

    @classmethod
    def leveldb_testpath(self):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    def test_search(self):
        # with no subcommand
        with patch('sys.stdout', new=StringIO()) as mock_print:
            res = CommandSearch().execute(None)
            self.assertFalse(res)
            self.assertIn("run `search help` to see supported queries", mock_print.getvalue())

        # with invalid command
        args = ['badcommand']
        res = CommandSearch().execute(args)
        self.assertFalse(res)

    def test_search_asset(self):
        # test no search parameter
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['asset']
            res = CommandSearch().execute(args)
            self.assertFalse(res)
            self.assertIn("run `search asset help` to see supported queries", mock_print.getvalue())

        # successful search asset NEO
        args = ['asset', "NEO"]
        res = CommandSearch().execute(args)
        self.assertTrue(res)

        # successful search asset gas
        args = ['asset', "gas"]
        res = CommandSearch().execute(args)
        self.assertTrue(res)

        # successful search asset NEOGas
        args = ['asset', "NEOGas"]
        res = CommandSearch().execute(args)
        self.assertTrue(res)

        # successful search asset AntShare
        args = ['asset', "AntShare"]
        res = CommandSearch().execute(args)
        self.assertTrue(res)

        # successful search asset AntCoin
        args = ['asset', "AntCoin"]
        res = CommandSearch().execute(args)
        self.assertTrue(res)

        # successful search by issuer and admin (same address)
        args = ['asset', "Abf2qMs1pzQb8kYk9RuxtUb9jtRKJVuBJt"]
        res = CommandSearch().execute(args)
        self.assertTrue(res)

        # unsuccessful search
        args = ['asset', 'blah']
        res = CommandSearch().execute(args)
        self.assertFalse(res)

    def test_search_contract(self):
        # test no search parameter
        with patch('sys.stdout', new=StringIO()) as mock_print:
            args = ['contract']
            res = CommandSearch().execute(args)
            self.assertFalse(res)
            self.assertIn("run `search contract help` to see supported queries", mock_print.getvalue())

        # successful search by name
        args = ['contract', "test NEX Template V4"]
        res = CommandSearch().execute(args)
        self.assertTrue(res)
        self.assertEqual(len(res), 1)

        # successful search by author
        args = ['contract', "dauTT"]
        res = CommandSearch().execute(args)
        self.assertTrue(res)
        self.assertEqual(len(res), 3)

        # successful search by description
        args = ['contract', "neo-ico-template"]
        res = CommandSearch().execute(args)
        self.assertTrue(res)
        self.assertEqual(len(res), 1)

        # successful search by email (as entered)
        args = ['contract', ""]
        res = CommandSearch().execute(args)
        self.assertTrue(res)
        self.assertEqual(len(res), 6)

        # bad search input
        args = ['contract', "blah"]
        res = CommandSearch().execute(args)
        self.assertFalse(res)
