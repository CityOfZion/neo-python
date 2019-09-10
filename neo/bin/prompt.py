#!/usr/bin/env python3

import argparse
import datetime
import os
import traceback
import asyncio
import termios
import sys
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import print_formatted_text, PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.application import get_app as prompt_toolkit_get_app
from neo import __version__
from neo.Core.Blockchain import Blockchain
from neo.Storage.Implementation.DBFactory import getBlockchainDB
from neo.Implementations.Notifications.NotificationDB import NotificationDB
from neo.Prompt.Commands.Wallet import CommandWallet
from neo.Prompt.Commands.Show import CommandShow
from neo.Prompt.Commands.Search import CommandSearch
from neo.Prompt.Commands.Config import CommandConfig
from neo.Prompt.Commands.SC import CommandSC
from neo.Prompt.PromptData import PromptData
from neo.Prompt.InputParser import InputParser
from neo.Settings import settings, PrivnetConnectionError
from neo.UserPreferences import preferences
from neo.logging import log_manager
from neo.Prompt.PromptPrinter import prompt_print, token_style
from neo.Network.nodemanager import NodeManager

import neo.Storage.Implementation.DBFactory as DBFactory

logger = log_manager.getLogger()

from prompt_toolkit.eventloop import use_asyncio_event_loop
from neo.Network.p2pservice import NetworkService
from contextlib import suppress


class PromptFileHistory(FileHistory):
    def append(self, string):
        string = self.redact_command(string)
        if len(string) == 0:
            return
        self.strings.append(string)

        # Save to file.
        with open(self.filename, 'ab') as f:
            def write(t):
                f.write(t.encode('utf-8'))

            write('\n# %s\n' % datetime.datetime.now())
            for line in string.split('\n'):
                write('+%s\n' % line)

    def redact_command(self, string):
        if len(string) == 0:
            return string
        command = [comm for comm in ['import wif', 'export wif', 'import nep2', 'export nep2'] if comm in string]
        if len(command) > 0:
            command = command[0]
            # only redacts command if wif/nep2 keys are in the command, not if the argument is left empty.
            if command in string and len(command + " ") < len(string):
                # example: import wif 5HueCGU8  -->  import wif <wif>
                return command + " <" + command.split(" ")[1] + ">"
            else:
                return string

        return string


class PromptInterface:
    prompt_completer = None
    history = None

    go_on = True

    wallet_loop_deferred = None

    Wallet = None

    _known_things = []

    _commands = [
        CommandWallet(), CommandShow(), CommandSearch(), CommandConfig(), CommandSC()
    ]

    _command_descs = [desc for c in _commands for desc in c.command_descs_with_sub_commands()]

    commands = {command.command_desc().command: command for command in _commands}

    start_height = None
    start_dt = None

    prompt_session = None

    def __init__(self, history_filename=None):
        PromptData.Prompt = self
        if history_filename:
            PromptInterface.history = PromptFileHistory(history_filename)

        self.input_parser = InputParser()
        self.start_height = Blockchain.Default().Height
        self.start_dt = datetime.datetime.utcnow()

    def get_bottom_toolbar(self, cli=None):
        out = []
        try:
            if PromptData.Wallet is None:
                return "[%s] Progress: 0/%s/%s" % (settings.net_name,
                                                   str(Blockchain.Default().Height),
                                                   str(Blockchain.Default().HeaderHeight))
            else:
                return "[%s] Progress: %s/%s/%s" % (settings.net_name, str(PromptData.Wallet._current_height),
                                                    str(Blockchain.Default().Height),
                                                    str(Blockchain.Default().HeaderHeight))
        except Exception as e:
            pass

        return out

    def get_completer(self):
        standard_completions = list({word for d in self._command_descs for word in d.command.split()})  # Use a set to ensure unicity of words
        standard_completions += ['quit', 'help', 'exit']

        if PromptData.Wallet:
            for addr in PromptData.Wallet.Addresses:
                if addr not in self._known_things:
                    self._known_things.append(addr)
            for alias in PromptData.Wallet.NamedAddr:
                if alias.Title not in self._known_things:
                    self._known_things.append(alias.Title)
            for tkn in PromptData.Wallet.GetTokens().values():
                if tkn.symbol not in self._known_things:
                    self._known_things.append(tkn.symbol)

        all_completions = standard_completions + self._known_things

        PromptInterface.prompt_completer = WordCompleter(all_completions)

        return PromptInterface.prompt_completer

    def quit(self):
        print('Shutting down. This may take a bit...')
        self.go_on = False
        PromptData.close_wallet()
        raise SystemExit

    def help(self):
        prompt_print(f"\nCommands:")
        for command_group in sorted(self.commands.keys()):
            command = self.commands[command_group]
            prompt_print(f"   {command_group:<15} - {command.command_desc().short_help}")
        prompt_print(f"\nRun 'COMMAND help' for more information on a command.")

    def on_looperror(self, err):
        logger.debug("On DB loop error! %s " % err)

    async def run(self):
        nodemgr = NodeManager()
        while not nodemgr.running:
            await asyncio.sleep(0.1)

        tokens = [("class:neo", 'NEO'), ("class:default", ' cli. Type '),
                  ("class:command", '\'help\' '), ("class:default", 'to get started')]

        print_formatted_text(FormattedText(tokens), style=token_style)

        print('\n')

        session = PromptSession("neo> ",
                                completer=self.get_completer(),
                                history=self.history,
                                bottom_toolbar=self.get_bottom_toolbar,
                                style=token_style,
                                refresh_interval=3,
                                )
        self.prompt_session = session
        result = ""

        while self.go_on:
            # with patch_stdout():
            try:
                result = await session.prompt(async_=True)
            except EOFError:
                # Control-D pressed: quit
                return self.quit()
            except KeyboardInterrupt:
                # Control-C pressed: pause for user input

                # temporarily mute stdout during user input
                # components like `network` set at DEBUG level will spam through the console
                # making it impractical to input user data
                log_manager.mute_stdio()

                print('Logging output muted during user input...')
                try:
                    result = await session.prompt(async_=True)
                except Exception as e:
                    logger.error("Exception handling input: %s " % e)

                # and re-enable stdio
                log_manager.unmute_stdio()
            except Exception as e:
                logger.error("Exception handling input: %s " % e)

            try:
                command, arguments = self.input_parser.parse_input(result)

                if command is not None and len(command) > 0:
                    command = command.lower()

                    if command in self.commands:
                        cmd = self.commands[command]

                        if len(arguments) > 0 and arguments[-1] == 'help':
                            cmd.handle_help(arguments)
                        else:
                            cmd.execute(arguments)
                    else:
                        if command == 'quit' or command == 'exit':
                            self.quit()
                        elif command == 'help':
                            self.help()
                        elif command is None:
                            print("Please specify a command")
                        else:
                            print("Command '%s' not found" % command)

            except Exception as e:

                print("Could not execute command: %s" % e)
                traceback.print_stack()
                traceback.print_exc()


def main():
    parser = argparse.ArgumentParser()

    # Network group
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-m", "--mainnet", action="store_true", default=False,
                       help="Use MainNet instead of the default TestNet")
    group.add_argument("-p", "--privnet", nargs="?", metavar="host", const=True, default=False,
                       help="Use a private net instead of the default TestNet, optionally using a custom host (default: 127.0.0.1)")
    group.add_argument("--coznet", action="store_true", default=False,
                       help="Use the CoZ network instead of the default TestNet")
    group.add_argument("-u", "--unittest", nargs="?", metavar="host", const=True, default=False,
                       help="Use a private net instead of the default TestNet, optionally using a custom host (default: 127.0.0.1)")
    group.add_argument("-c", "--config", action="store", help="Use a specific config file")

    # Theme
    parser.add_argument("-t", "--set-default-theme", dest="theme",
                        choices=["dark", "light"],
                        help="Set the default theme to be loaded from the config file. Default: 'dark'")

    # Verbose
    parser.add_argument("-v", "--verbose", action="store_true", default=False,
                        help="Show smart-contract events by default")

    # Where to store stuff
    parser.add_argument("--datadir", action="store",
                        help="Absolute path to use for database directories")

    # peers
    parser.add_argument("--minpeers", action="store", type=int, choices=range(1, 10 + 1), metavar="[1-10]",
                        help="Min peers to use for P2P Joining")

    parser.add_argument("--maxpeers", action="store", type=int, default=5, choices=range(1, 10 + 1), metavar="[1-10]",
                        help="Max peers to use for P2P Joining")

    # Show the neo-python version
    parser.add_argument("--version", action="version",
                        version="neo-python v{version}".format(version=__version__))

    args = parser.parse_args()

    # Setting the datadir must come before setting the network, else the wrong path is checked at net setup.
    if args.datadir:
        settings.set_data_dir(args.datadir)

    # Setup depending on command line arguments. By default, the testnet settings are already loaded.
    if args.config:
        settings.setup(args.config)
    elif args.mainnet:
        settings.setup_mainnet()
    elif args.privnet:
        try:
            settings.setup_privnet(args.privnet)
        except PrivnetConnectionError as e:
            logger.error(str(e))
            return
    elif args.coznet:
        settings.setup_coznet()
    elif args.unittest:
        settings.setup_unittest_net()

    # Logfile settings & setup
    logfile_fn = os.path.join(settings.DATA_DIR_PATH, 'prompt.log')
    logfile_max_bytes = 5e7  # 50 MB
    logfile_backup_count = 3  # 3 logfiles history
    settings.set_logfile(logfile_fn, logfile_max_bytes, logfile_backup_count)

    if args.theme:
        preferences.set_theme(args.theme)

    if args.verbose:
        settings.set_log_smart_contract_events(True)

    def set_min_peers(num_peers) -> bool:
        try:
            settings.set_min_peers(num_peers)
            print("Minpeers set to ", num_peers)
            return True
        except ValueError:
            print("Please supply a positive integer for minpeers")
            return False

    def set_max_peers(num_peers) -> bool:
        try:
            settings.set_max_peers(num_peers)
            print("Maxpeers set to ", num_peers)
            return True
        except ValueError:
            print("Please supply a positive integer for maxpeers")
            return False

    minpeers = args.minpeers
    maxpeers = args.maxpeers

    if minpeers and maxpeers:
        if minpeers > maxpeers:
            print("minpeers setting cannot be bigger than maxpeers setting")
            return
        if not set_min_peers(minpeers) or not set_max_peers(maxpeers):
            return
    elif minpeers:
        if not set_min_peers(minpeers):
            return
        if minpeers > settings.CONNECTED_PEER_MAX:
            if not set_max_peers(minpeers):
                return
    elif maxpeers:
        if not set_max_peers(maxpeers):
            return
        if maxpeers < settings.CONNECTED_PEER_MIN:
            if not set_min_peers(maxpeers):
                return

    loop = asyncio.get_event_loop()
    # put prompt_toolkit on top of asyncio to avoid blocking
    use_asyncio_event_loop()

    # Instantiate the blockchain and subscribe to notifications
    blockchain = Blockchain(DBFactory.getBlockchainDB(settings.chain_leveldb_path))
    Blockchain.RegisterBlockchain(blockchain)

    # Try to set up a notification db
    if NotificationDB.instance():
        NotificationDB.instance().start()

    # Start the prompt interface
    fn_prompt_history = os.path.join(settings.DATA_DIR_PATH, '.prompt.py.history')
    cli = PromptInterface(fn_prompt_history)

    cli_task = loop.create_task(cli.run())
    p2p = NetworkService()
    loop.create_task(p2p.start())

    async def shutdown():
        all_tasks = asyncio.all_tasks()
        for task in all_tasks:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    # prompt_toolkit hack for not cleaning up see: https://github.com/prompt-toolkit/python-prompt-toolkit/issues/787
    old_attrs = termios.tcgetattr(sys.stdin)

    try:
        loop.run_forever()
    except SystemExit:
        pass
    finally:
        with suppress(asyncio.InvalidStateError):
            app = prompt_toolkit_get_app()
            if app.is_running:
                app.exit()
        with suppress((SystemExit, Exception)):
            cli_task.exception()
        loop.run_until_complete(p2p.shutdown())
        loop.run_until_complete(shutdown())
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.stop()
        loop.close()

    # Run things

    # After the reactor is stopped, gracefully shutdown the database.
    NotificationDB.close()
    Blockchain.Default().Dispose()

    # clean up prompt_toolkit mess, see above
    termios.tcsetattr(sys.stdin, termios.TCSANOW, old_attrs)


if __name__ == "__main__":
    main()
