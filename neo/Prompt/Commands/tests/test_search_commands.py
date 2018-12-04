import os
from neo.Settings import settings
from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.Prompt.Commands.Search import CommandSearch
from neo.Prompt.PromptData import PromptData
from neo.bin.prompt import PromptInterface


class CommandShowTestCase(BlockchainFixtureTestCase):

    @classmethod
    def leveldb_testpath(self):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    @classmethod
    def tearDown(cls):
        PromptData.Prompt = None

    def test_search(self):
        # with no subcommand
        res = CommandSearch().execute(None)
        self.assertFalse(res)

        # with invalid command
        args = ['badcommand']
        res = CommandSearch().execute(args)
        self.assertFalse(res)

    def test_search_asset(self):
        # setup
        PromptInterface()

        # successful search by name
        args = ['asset', "AntShare"]
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
        # setup
        PromptInterface()

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