#!/usr/bin/env python3

import argparse
import datetime
import os
import traceback
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import print_formatted_text, PromptSession
from prompt_toolkit.formatted_text import FormattedText
from twisted.internet import reactor, task
from neo import __version__
from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB
from neo.Network.NodeLeader import NodeLeader
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

logger = log_manager.getLogger()


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
            return "[%s] Progress: %s/%s" % (settings.net_name,
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
        Blockchain.Default().Dispose()
        NodeLeader.Instance().Shutdown()
        reactor.stop()

    def help(self):
        prompt_print(f"\nCommands:")
        for command_group in sorted(self.commands.keys()):
            command = self.commands[command_group]
            prompt_print(f"   {command_group:<15} - {command.command_desc().short_help}")
        prompt_print(f"\nRun 'COMMAND help' for more information on a command.")

    def start_wallet_loop(self):
        if self.wallet_loop_deferred:
            self.stop_wallet_loop()
        self.walletdb_loop = task.LoopingCall(PromptData.Wallet.ProcessBlocks)
        self.wallet_loop_deferred = self.walletdb_loop.start(1)
        self.wallet_loop_deferred.addErrback(self.on_looperror)

    def stop_wallet_loop(self):
        self.wallet_loop_deferred.cancel()
        self.wallet_loop_deferred = None
        if self.walletdb_loop and self.walletdb_loop.running:
            self.walletdb_loop.stop()

    def on_looperror(self, err):
        logger.debug("On DB loop error! %s " % err)

    def run(self):
        dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
        dbloop_deferred = dbloop.start(.1)
        dbloop_deferred.addErrback(self.on_looperror)

        tokens = [("class:neo", 'NEO'), ("class:default", ' cli. Type '),
                  ("class:command", '\'help\' '), ("class:default", 'to get started')]

        print_formatted_text(FormattedText(tokens), style=token_style)

        print('\n')

        while self.go_on:

            session = PromptSession("neo> ",
                                    completer=self.get_completer(),
                                    history=self.history,
                                    bottom_toolbar=self.get_bottom_toolbar,
                                    style=token_style,
                                    refresh_interval=3,
                                    )

            try:
                result = session.prompt()
            except EOFError:
                # Control-D pressed: quit
                return self.quit()
            except KeyboardInterrupt:
                # Control-C pressed: do nothing
                continue
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
    parser.add_argument("--maxpeers", action="store", default=5,
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

    if args.maxpeers:
        settings.set_max_peers(args.maxpeers)

    # Instantiate the blockchain and subscribe to notifications
    blockchain = LevelDBBlockchain(settings.chain_leveldb_path)
    Blockchain.RegisterBlockchain(blockchain)

    # Try to set up a notification db
    if NotificationDB.instance():
        NotificationDB.instance().start()

    # Start the prompt interface
    fn_prompt_history = os.path.join(settings.DATA_DIR_PATH, '.prompt.py.history')
    cli = PromptInterface(fn_prompt_history)

    # Run things

    reactor.callInThread(cli.run)

    NodeLeader.Instance().Start()

    # reactor.run() is blocking, until `quit()` is called which stops the reactor.
    reactor.run()

    # After the reactor is stopped, gracefully shutdown the database.
    NotificationDB.close()
    Blockchain.Default().Dispose()
    NodeLeader.Instance().Shutdown()


if __name__ == "__main__":
    main()
