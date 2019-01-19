from neo.logging import log_manager
from neo.Prompt.Commands.Config import start_output_config
from mock import patch
from neo.Utils.NeoTestCase import NeoTestCase
from neo.Prompt.PromptPrinter import pp
import logging
import io


class TestOutputConfig(NeoTestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('neo.Prompt.Commands.Config.log_manager.config_stdio')
    @patch('neo.Prompt.Commands.Config.prompt')
    def test_setting_levels(self, mocked_prompt, mocked_config_stdio, mocked_stdout):
        # we mocked stdout such that we can mute the print statements. We don't need to see them in the tests

        # reset current loggers to have a clean slate
        log_manager.loggers = dict()
        # setup logging for 3 components
        logger_generic = log_manager.getLogger()
        logger_network = log_manager.getLogger('network')
        logger_db = log_manager.getLogger('db')

        # we expect to be prompted for 3 components (generic, network and db) setup at INFO level by default
        # and then we choose option 1 twice (option 1 = DEBUG level) and something invalid the 3rd time.
        mocked_prompt.side_effect = ['1', '1', 'nope']
        start_output_config()

        # then we assert that for `generic` and `network` we te to configure the level to DEBUG
        # and for `db` we find no entry because it was an invalid choice.
        # Invalid or `enter` as choice means keep as is
        mocked_config_stdio.assert_called_with([('generic', logging.DEBUG), ('network', logging.DEBUG)])
