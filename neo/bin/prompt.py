#!/usr/bin/env python3

import argparse
import datetime
import json
import os
import psutil
import traceback
import logging
import sys
from logzero import logger
from prompt_toolkit import prompt
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import print_tokens
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token
from twisted.internet import reactor, task

from neo import __version__
from neo.Core.Blockchain import Blockchain
from neocore.Fixed8 import Fixed8
from neo.IO.MemoryStream import StreamManager
from neo.Wallets.utils import to_aes_key
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Implementations.Blockchains.LevelDB.DebugStorage import DebugStorage
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB
from neo.Network.NodeLeader import NodeLeader
from neo.Prompt.Commands.BuildNRun import BuildAndRun, LoadAndRun
from neo.Prompt.Commands.Invoke import InvokeContract, TestInvokeContract, test_invoke
from neo.Prompt.Commands.LoadSmartContract import LoadContract, GatherContractDetails, ImportContractAddr, \
    ImportMultiSigContractAddr
from neo.Prompt.Commands.Send import construct_and_send, parse_and_sign
from neo.contrib.nex.withdraw import RequestWithdrawFrom, PrintHolds, DeleteHolds, WithdrawOne, WithdrawAll, \
    CancelWithdrawalHolds, ShowCompletedHolds, CleanupCompletedHolds
from neo.Prompt.Commands.Tokens import token_approve_allowance, token_get_allowance, token_send, token_send_from, \
    token_mint, token_crowdsale_register
from neo.Prompt.Commands.Wallet import DeleteAddress, ImportWatchAddr, ImportToken, ClaimGas, DeleteToken, AddAlias, \
    ShowUnspentCoins
from neo.Prompt.Utils import get_arg
from neo.Prompt.InputParser import InputParser
from neo.Settings import settings, PrivnetConnectionError, PATH_USER_DATA
from neo.UserPreferences import preferences
from neocore.KeyPair import KeyPair
from neocore.UInt256 import UInt256

# Logfile settings & setup
LOGFILE_FN = os.path.join(PATH_USER_DATA, 'prompt.log')
LOGFILE_MAX_BYTES = 5e7  # 50 MB
LOGFILE_BACKUP_COUNT = 3  # 3 logfiles history
settings.set_logfile(LOGFILE_FN, LOGFILE_MAX_BYTES, LOGFILE_BACKUP_COUNT)

# Prompt history filename
FILENAME_PROMPT_HISTORY = os.path.join(PATH_USER_DATA, '.prompt.py.history')


class PromptInterface(object):
    go_on = True

    _walletdb_loop = None

    Wallet = None

    _known_things = []

    commands = ['quit',
                'help',
                'block {index/hash} (tx)',
                'header {index/hash}',
                'tx {hash}',
                'asset {assetId}',
                'asset search {query}',
                'contract {contract hash}',
                'contract search {query}',
                'notifications {block_number or address}',
                'mem',
                'nodes',
                'state',
                'config debug {on/off}',
                'config sc-events {on/off}',
                'build {path/to/file.py} (test {params} {returntype} {needs_storage} {needs_dynamic_invoke} {test_params})',
                'load_run {path/to/file.avm} (test {params} {returntype} {needs_storage} {needs_dynamic_invoke} {test_params})',
                'import wif {wif}',
                'import nep2 {nep2_encrypted_key}',
                'import contract {path/to/file.avm} {params} {returntype} {needs_storage} {needs_dynamic_invoke}',
                'import contract_addr {contract_hash} {pubkey}',
                'import multisig_addr {pubkey in wallet} {minimum # of signatures required} {signing pubkey 1} {signing pubkey 2}...',
                'import watch_addr {address}',
                'import token {token_contract_hash}',
                'export wif {address}',
                'export nep2 {address}',
                'open wallet {path}',
                'create wallet {path}',
                'wallet {verbose}',
                'wallet claim',
                'wallet migrate',
                'wallet rebuild {start block}',
                'wallet delete_addr {addr}',
                'wallet alias {addr} {title}',
                'wallet tkn_send {token symbol} {address_from} {address to} {amount} ',
                'wallet tkn_send_from {token symbol} {address_from} {address to} {amount}',
                'wallet tkn_approve {token symbol} {address_from} {address to} {amount}',
                'wallet tkn_allowance {token symbol} {address_from} {address to}',
                'wallet tkn_mint {token symbol} {mint_to_addr} (--attach-neo={amount}, --attach-gas={amount})',
                'wallet unspent',
                'wallet close',
                'withdraw_request {asset_name} {contract_hash} {to_addr} {amount}',
                'withdraw holds # lists all current holds',
                'withdraw completed # lists completed holds eligible for cleanup',
                'withdraw cancel # cancels current holds',
                'withdraw cleanup # cleans up completed holds',
                'withdraw # withdraws the first hold availabe',
                'withdraw all # withdraw all holds available',
                'send {assetId or name} {address} {amount} (--from-addr={addr})',
                'sign {transaction in JSON format}',
                'testinvoke {contract hash} {params} (--attach-neo={amount}, --attach-gas={amount})',
                'debugstorage {on/off/reset}'
                ]

    history = FileHistory(FILENAME_PROMPT_HISTORY)

    token_style = None
    start_height = None
    start_dt = None

    def __init__(self):
        self.input_parser = InputParser()
        self.start_height = Blockchain.Default().Height
        self.start_dt = datetime.datetime.utcnow()

        self.token_style = style_from_dict({
            Token.Command: preferences.token_style['Command'],
            Token.Neo: preferences.token_style['Neo'],
            Token.Default: preferences.token_style['Default'],
            Token.Number: preferences.token_style['Number'],
        })

    def get_bottom_toolbar(self, cli=None):
        out = []
        try:
            out = [(Token.Command, '[%s] Progress: ' % settings.net_name),
                   (Token.Number, str(Blockchain.Default().Height)),
                   (Token.Neo, '/'),
                   (Token.Number, str(Blockchain.Default().HeaderHeight))]
        except Exception as e:
            pass

        return out

    def get_completer(self):

        standard_completions = ['block', 'tx', 'header', 'mem', 'neo', 'gas',
                                'help', 'state', 'nodes', 'exit', 'quit',
                                'config', 'import', 'export', 'open',
                                'wallet', 'contract', 'asset', 'wif',
                                'watch_addr', 'contract_addr', 'testinvoke', 'tkn_send',
                                'tkn_mint', 'tkn_send_from', 'tkn_approve', 'tkn_allowance',
                                'build', 'notifications', ]

        if self.Wallet:
            for addr in self.Wallet.Addresses:
                if addr not in self._known_things:
                    self._known_things.append(addr)
            for alias in self.Wallet.NamedAddr:
                if alias.Title not in self._known_things:
                    self._known_things.append(alias.Title)
            for tkn in self.Wallet.GetTokens().values():
                if tkn.symbol not in self._known_things:
                    self._known_things.append(tkn.symbol)

        all_completions = standard_completions + self._known_things

        completer = WordCompleter(all_completions)

        return completer

    def quit(self):
        print('Shutting down. This may take a bit...')
        self.go_on = False
        self.do_close_wallet()
        reactor.stop()

    def help(self):
        tokens = []
        for c in self.commands:
            tokens.append((Token.Command, "%s\n" % c))
        print_tokens(tokens, self.token_style)

    def do_open(self, arguments):
        if self.Wallet:
            self.do_close_wallet()

        item = get_arg(arguments)

        if item and item == 'wallet':

            path = get_arg(arguments, 1)

            if path:

                if not os.path.exists(path):
                    print("Wallet file not found")
                    return

                passwd = prompt("[password]> ", is_password=True)
                password_key = to_aes_key(passwd)

                try:
                    self.Wallet = UserWallet.Open(path, password_key)

                    self._walletdb_loop = task.LoopingCall(self.Wallet.ProcessBlocks)
                    self._walletdb_loop.start(1)
                    print("Opened wallet at %s" % path)
                except Exception as e:
                    print("Could not open wallet: %s" % e)

            else:
                print("Please specify a path")
        else:
            print("Please specify something to open")

    def do_create(self, arguments):
        item = get_arg(arguments)

        if item and item == 'wallet':

            path = get_arg(arguments, 1)

            if path:

                if os.path.exists(path):
                    print("File already exists")
                    return

                passwd1 = prompt("[password]> ", is_password=True)
                passwd2 = prompt("[password again]> ", is_password=True)

                if passwd1 != passwd2 or len(passwd1) < 10:
                    print("Please provide matching passwords that are at least 10 characters long")
                    return

                password_key = to_aes_key(passwd1)

                try:
                    self.Wallet = UserWallet.Create(path=path,
                                                    password=password_key)
                    contract = self.Wallet.GetDefaultContract()
                    key = self.Wallet.GetKey(contract.PublicKeyHash)
                    print("Wallet %s" % json.dumps(self.Wallet.ToJson(), indent=4))
                    print("Pubkey %s" % key.PublicKey.encode_point(True))
                except Exception as e:
                    print("Exception creating wallet: %s" % e)
                    self.Wallet = None
                    if os.path.isfile(path):
                        try:
                            os.remove(path)
                        except Exception as e:
                            print("Could not remove {}: {}".format(path, e))
                    return

                if self.Wallet:
                    self._walletdb_loop = task.LoopingCall(self.Wallet.ProcessBlocks)
                    self._walletdb_loop.start(1)

            else:
                print("Please specify a path")

    def do_close_wallet(self):
        if self.Wallet:
            path = self.Wallet._path
            self._walletdb_loop.stop()
            self._walletdb_loop = None
            self.Wallet.Close()
            self.Wallet = None
            print("Closed wallet %s" % path)

    def do_import(self, arguments):
        item = get_arg(arguments)

        if not item:
            print("Please specify something to import")
            return

        if item == 'wif':
            if not self.Wallet:
                print("Please open a wallet before importing WIF")
                return

            wif = get_arg(arguments, 1)
            if not wif:
                print("Please supply a valid WIF key")
                return

            try:
                prikey = KeyPair.PrivateKeyFromWIF(wif)
                key = self.Wallet.CreateKey(prikey)
                print("Imported key: %s" % wif)
                print("Pubkey: %s\n" % key.PublicKey.encode_point(True).hex())
                print("Wallet: %s" % json.dumps(self.Wallet.ToJson(), indent=4))
            except ValueError as e:
                print(str(e))
            except Exception as e:
                print(str(e))

            return

        elif item == 'nep2':
            if not self.Wallet:
                print("Please open a wallet before importing a NEP2 key")
                return

            nep2_key = get_arg(arguments, 1)
            if not nep2_key:
                print("Please supply a valid NEP2 encrypted private key")
                return

            nep2_passwd = prompt("[key password]> ", is_password=True)

            try:
                prikey = KeyPair.PrivateKeyFromNEP2(nep2_key, nep2_passwd)
                key = self.Wallet.CreateKey(prikey)
                print("Imported NEP2 key: %s" % nep2_key)
                print("Pubkey: %s\n" % key.PublicKey.encode_point(True).hex())
                print("Wallet: %s" % json.dumps(self.Wallet.ToJson(), indent=4))
            except ValueError as e:
                print(str(e))
            except Exception as e:
                print(str(e))

            return

        elif item == 'contract':
            return self.load_smart_contract(arguments)

        elif item == 'contract_addr':
            return ImportContractAddr(self.Wallet, arguments[1:])

        elif item == 'watch_addr':
            return ImportWatchAddr(self.Wallet, get_arg(arguments, 1))

        elif item == 'multisig_addr':
            return ImportMultiSigContractAddr(self.Wallet, arguments[1:])

        elif item == 'token':
            return ImportToken(self.Wallet, get_arg(arguments, 1))

        else:
            print("Import of '%s' not implemented" % item)

    def do_build(self, arguments):
        BuildAndRun(arguments, self.Wallet)

    def do_load_n_run(self, arguments):
        LoadAndRun(arguments, self.Wallet)

    def do_export(self, arguments):
        item = get_arg(arguments)

        if item == 'wif':
            if not self.Wallet:
                return print("Please open a wallet")

            address = get_arg(arguments, 1)
            if not address:
                return print("Please specify an address")

            passwd = prompt("[wallet password]> ", is_password=True)
            if not self.Wallet.ValidatePassword(passwd):
                return print("Incorrect password")

            keys = self.Wallet.GetKeys()
            for key in keys:
                if key.GetAddress() == address:
                    export = key.Export()
                    print("WIF key export: %s" % export)
            return

        elif item == 'nep2':
            if not self.Wallet:
                return print("Please open a wallet")

            address = get_arg(arguments, 1)
            if not address:
                return print("Please specify an address")

            passwd = prompt("[wallet password]> ", is_password=True)
            if not self.Wallet.ValidatePassword(passwd):
                return print("Incorrect password")

            nep2_passwd1 = prompt("[key password]> ", is_password=True)
            if len(nep2_passwd1) < 10:
                return print("Please provide a password with at least 10 characters")

            nep2_passwd2 = prompt("[key password again]> ", is_password=True)
            if nep2_passwd1 != nep2_passwd2:
                return print("Passwords do not match")

            keys = self.Wallet.GetKeys()
            for key in keys:
                export = key.ExportNEP2(nep2_passwd1)
                print("NEP2 key export: %s" % export)
            return

        print("Command export %s not found" % item)

    def make_withdraw_request(self, arguments):
        if not self.Wallet:
            print("Please open a wallet")
            return
        if len(arguments) == 4:
            RequestWithdrawFrom(self.Wallet, arguments[0], arguments[1], arguments[2], arguments[3])
        else:
            print("Incorrect arg length. Use 'withdraw_request {asset_id} {contract_hash} {to_addr} {amount}'")

    def do_withdraw(self, arguments):
        if not self.Wallet:
            print("Please open a wallet")
            return

        item = get_arg(arguments, 0)

        if item:

            if item == 'holds':
                PrintHolds(self.Wallet)
            elif item == 'delete_holds':
                index_to_delete = -1
                if get_arg(arguments, 1) and int(get_arg(arguments, 1)) > -1:
                    index_to_delete = int(get_arg(arguments, 1))
                DeleteHolds(self.Wallet, index_to_delete)
            elif item == 'cancel_holds':
                if len(arguments) > 1:
                    CancelWithdrawalHolds(self.Wallet, get_arg(arguments, 1))
                else:
                    print("Please specify contract hash to cancel holds for")
            elif item == 'completed':
                ShowCompletedHolds(self.Wallet)
            elif item == 'cleanup':
                CleanupCompletedHolds(self.Wallet)
            elif item == 'all':
                WithdrawAll(self.Wallet)
        else:
            WithdrawOne(self.Wallet)

    def do_notifications(self, arguments):
        if NotificationDB.instance() is None:
            print("No notification DB Configured")
            return

        item = get_arg(arguments, 0)
        events = []
        if len(item) == 34:
            addr = item
            events = NotificationDB.instance().get_by_addr(addr)
        else:
            try:
                block_height = int(item)
                if block_height < Blockchain.Default().Height:
                    events = NotificationDB.instance().get_by_block(block_height)
                else:
                    print("Block %s not found" % block_height)
                    return
            except Exception as e:
                print("Could not parse block height %s" % e)
                return

        if len(events):
            [print(json.dumps(e.ToJson(), indent=4)) for e in events]
        else:
            print("No events found for %s" % item)

    def show_wallet(self, arguments):
        if not self.Wallet:
            print("Please open a wallet")
            return

        item = get_arg(arguments)

        if not item:
            print("Wallet %s " % json.dumps(self.Wallet.ToJson(), indent=4))
            return

        if item in ['v', '--v', 'verbose']:
            print("Wallet %s " % json.dumps(self.Wallet.ToJson(verbose=True), indent=4))
            return
        elif item == 'migrate' and self.Wallet is not None:
            self.Wallet.Migrate()
            print("Migrated wallet")
        elif item == 'delete_addr':
            addr_to_delete = get_arg(arguments, 1)
            DeleteAddress(self, self.Wallet, addr_to_delete)
        elif item == 'delete_token':
            token_to_delete = get_arg(arguments, 1)
            DeleteToken(self.Wallet, token_to_delete)
        elif item == 'close':
            self.do_close_wallet()
        elif item == 'claim':
            ClaimGas(self.Wallet, True, arguments[1:])
        elif item == 'rebuild':
            self.Wallet.Rebuild()
            try:
                item2 = int(get_arg(arguments, 1))
                if item2 and item2 > 0:
                    print("Restarting at %s" % item2)
                    self.Wallet._current_height = item2
            except Exception as e:
                pass
        elif item == 'tkn_send':
            token_send(self.Wallet, arguments[1:])
        elif item == 'tkn_send_from':
            token_send_from(self.Wallet, arguments[1:])
        elif item == 'tkn_approve':
            token_approve_allowance(self.Wallet, arguments[1:])
        elif item == 'tkn_allowance':
            token_get_allowance(self.Wallet, arguments[1:], verbose=True)
        elif item == 'tkn_mint':
            token_mint(self.Wallet, arguments[1:])
        elif item == 'tkn_register':
            token_crowdsale_register(self.Wallet, arguments[1:])
        elif item == 'unspent':
            ShowUnspentCoins(self.Wallet, arguments[1:])
        elif item == 'alias':
            if len(arguments) == 3:
                AddAlias(self.Wallet, arguments[1], arguments[2])
            else:
                print("Please supply an address and title")
        else:
            print("Wallet: '{}' is an invalid parameter".format(item))

    def do_send(self, arguments):
        construct_and_send(self, self.Wallet, arguments)

    def do_sign(self, arguments):
        jsn = get_arg(arguments)
        parse_and_sign(self, self.Wallet, jsn)

    def show_state(self):
        height = Blockchain.Default().Height
        headers = Blockchain.Default().HeaderHeight

        diff = height - self.start_height
        now = datetime.datetime.utcnow()
        difftime = now - self.start_dt

        mins = difftime / datetime.timedelta(minutes=1)

        bpm = 0
        if diff > 0 and mins > 0:
            bpm = diff / mins

        out = "Progress: %s / %s\n" % (height, headers)
        out += "Block-cache length %s\n" % Blockchain.Default().BlockCacheCount
        out += "Blocks since program start %s\n" % diff
        out += "Time elapsed %s mins\n" % mins
        out += "Blocks per min %s \n" % bpm
        tokens = [(Token.Number, out)]
        print_tokens(tokens, self.token_style)

    def show_nodes(self):
        if len(NodeLeader.Instance().Peers) > 0:
            out = ""
            for peer in NodeLeader.Instance().Peers:
                out += "Peer %s - IO: %s\n" % (peer.Name(), peer.IOStats())
            print_tokens([(Token.Number, out)], self.token_style)
        else:
            print("Not connected yet\n")

    def show_block(self, args):
        item = get_arg(args)
        txarg = get_arg(args, 1)
        if item is not None:
            block = Blockchain.Default().GetBlock(item)

            if block is not None:

                bjson = json.dumps(block.ToJson(), indent=4)
                tokens = [(Token.Number, bjson)]
                print_tokens(tokens, self.token_style)
                print('\n')
                if txarg and 'tx' in txarg:

                    for tx in block.FullTransactions:
                        print(json.dumps(tx.ToJson(), indent=4))

            else:
                print("Could not locate block %s" % item)
        else:
            print("please specify a block")

    def show_header(self, args):
        item = get_arg(args)
        if item is not None:
            header = Blockchain.Default().GetHeaderBy(item)
            if header is not None:
                print(json.dumps(header.ToJson(), indent=4))
            else:
                print("Could not locate header %s\n" % item)
        else:
            print("Please specify a header")

    def show_tx(self, args):
        if len(args):
            try:
                txid = UInt256.ParseString(get_arg(args))
                tx, height = Blockchain.Default().GetTransaction(txid)
                if height > -1:
                    jsn = tx.ToJson()
                    jsn['height'] = height
                    jsn['unspents'] = [uns.ToJson(tx.outputs.index(uns)) for uns in Blockchain.Default().GetAllUnspent(txid)]
                    tokens = [(Token.Command, json.dumps(jsn, indent=4))]
                    print_tokens(tokens, self.token_style)
                    print('\n')
            except Exception as e:
                print("Could not find transaction from args: %s (%s)" % (e, args))
        else:
            print("Please specify a TX hash")

    def show_account_state(self, args):
        item = get_arg(args)

        if item is not None:
            account = Blockchain.Default().GetAccountState(item, print_all_accounts=True)

            if account is not None:
                bjson = json.dumps(account.ToJson(), indent=4)
                tokens = [(Token.Number, bjson)]
                print_tokens(tokens, self.token_style)
                print('\n')
            else:
                print("Account %s not found" % item)
        else:
            print("Please specify an account address")

    def show_asset_state(self, args):
        item = get_arg(args)

        if item is not None:

            if item == 'search':
                query = get_arg(args, 1)
                results = Blockchain.Default().SearchAssetState(query)
                print("Found %s results for %s" % (len(results), query))
                for asset in results:
                    bjson = json.dumps(asset.ToJson(), indent=4)
                    tokens = [(Token.Number, bjson)]
                    print_tokens(tokens, self.token_style)
                    print('\n')

                return

            asset = Blockchain.Default().GetAssetState(item)

            if asset is not None:
                bjson = json.dumps(asset.ToJson(), indent=4)
                tokens = [(Token.Number, bjson)]
                print_tokens(tokens, self.token_style)
                print('\n')
            else:
                print("Asset %s not found" % item)
        else:
            print("Please specify an asset hash")

    def show_contract_state(self, args):
        item = get_arg(args)

        if item is not None:

            if item.lower() == 'all':
                contracts = Blockchain.Default().ShowAllContracts()
                print("Contracts: %s" % contracts)
            elif item.lower() == 'search':
                query = get_arg(args, 1)
                if query:

                    contracts = Blockchain.Default().SearchContracts(query=query)
                    print("Found %s results for %s" % (len(contracts), query))
                    for contract in contracts:
                        bjson = json.dumps(contract.ToJson(), indent=4)
                        tokens = [(Token.Number, bjson)]
                        print_tokens(tokens, self.token_style)
                        print('\n')
                else:
                    print("Please specify a search query")
            else:
                contract = Blockchain.Default().GetContract(item)

                if contract is not None:
                    contract.DetermineIsNEP5()
                    jsn = contract.ToJson()
                    bjson = json.dumps(jsn, indent=4)
                    tokens = [(Token.Number, bjson)]
                    print_tokens(tokens, self.token_style)
                    print('\n')
        else:
            print("Please specify a contract")

    def test_invoke_contract(self, args):
        if not self.Wallet:
            print("Please open a wallet")
            return

        if args and len(args) > 0:
            tx, fee, results, num_ops = TestInvokeContract(self.Wallet, args)

            if tx is not None and results is not None:
                print(
                    "\n-------------------------------------------------------------------------------------------------------------------------------------")
                print("Test invoke successful")
                print("Total operations: %s" % num_ops)
                print("Results %s" % [str(item) for item in results])
                print("Invoke TX GAS cost: %s" % (tx.Gas.value / Fixed8.D))
                print("Invoke TX fee: %s" % (fee.value / Fixed8.D))
                print(
                    "-------------------------------------------------------------------------------------------------------------------------------------\n")
                print("Enter your password to continue and invoke on the network\n")

                passwd = prompt("[password]> ", is_password=True)
                if not self.Wallet.ValidatePassword(passwd):
                    return print("Incorrect password")

                result = InvokeContract(self.Wallet, tx, fee)

                return
            else:
                print("Error testing contract invoke")
                return

        print("Please specify a contract to invoke")

    def load_smart_contract(self, args):
        if not self.Wallet:
            print("Please open a wallet")
            return

        function_code = LoadContract(args[1:])

        if function_code:

            contract_script = GatherContractDetails(function_code, self)

            if contract_script is not None:

                tx, fee, results, num_ops = test_invoke(contract_script, self.Wallet, [])

                if tx is not None and results is not None:
                    print(
                        "\n-------------------------------------------------------------------------------------------------------------------------------------")
                    print("Test deploy invoke successful")
                    print("Total operations executed: %s " % num_ops)
                    print("Results:")
                    print([item.GetInterface() for item in results])
                    print("Deploy Invoke TX GAS cost: %s " % (tx.Gas.value / Fixed8.D))
                    print("Deploy Invoke TX Fee: %s " % (fee.value / Fixed8.D))
                    print(
                        "-------------------------------------------------------------------------------------------------------------------------------------\n")
                    print("Enter your password to continue and deploy this contract")

                    passwd = prompt("[password]> ", is_password=True)
                    if not self.Wallet.ValidatePassword(passwd):
                        return print("Incorrect password")

                    result = InvokeContract(self.Wallet, tx, Fixed8.Zero())

                    return
                else:
                    print("Test invoke failed")
                    print("TX is %s, results are %s" % (tx, results))
                    return

    def show_mem(self):
        process = psutil.Process(os.getpid())
        total = process.memory_info().rss
        totalmb = total / (1024 * 1024)
        out = "Total: %s MB\n" % totalmb
        out += "Total buffers: %s\n" % StreamManager.TotalBuffers()
        print_tokens([(Token.Number, out)], self.token_style)

    def handle_debug_storage(self, args):
        what = get_arg(args)

        if what == 'on':
            settings.USE_DEBUG_STORAGE = True
            print("Debug storage on")
        elif what == 'off':
            settings.USE_DEBUG_STORAGE = False
            print("Debug Storage off")
        elif what == 'reset':
            DebugStorage.instance().reset()
            print("Reset debug storage")
        else:
            print("Please specify on|off|reset")

    def configure(self, args):
        what = get_arg(args)

        if what == 'debug':
            c1 = get_arg(args, 1).lower()
            if c1 is not None:
                if c1 == 'on' or c1 == '1':
                    print("Debug logging is now enabled")
                    settings.set_loglevel(logging.DEBUG)
                if c1 == 'off' or c1 == '0':
                    print("Debug logging is now disabled")
                    settings.set_loglevel(logging.INFO)

            else:
                print("Cannot configure log. Please specify on|off")

        elif what == 'sc-events':
            c1 = get_arg(args, 1).lower()
            if c1 is not None:
                if c1 == 'on' or c1 == '1':
                    print("Smart contract event logging is now enabled")
                    settings.set_log_smart_contract_events(True)
                if c1 == 'off' or c1 == '0':
                    print("Smart contract event logging is now disabled")
                    settings.set_log_smart_contract_events(False)

            else:
                print("Cannot configure log. Please specify on|off")

        elif what == 'sc-debug-notify':
            c1 = get_arg(args, 1).lower()
            if c1 is not None:
                if c1 == 'on' or c1 == '1':
                    print("Smart contract emit Notify events on execution failure is now enabled")
                    settings.set_emit_notify_events_on_sc_execution_error(True)
                if c1 == 'off' or c1 == '0':
                    print("Smart contract emit Notify events on execution failure is now disabled")
                    settings.set_emit_notify_events_on_sc_execution_error(False)

            else:
                print("Cannot configure log. Please specify on|off")

        elif what == 'vm-log':
            c1 = get_arg(args, 1).lower()
            if c1 is not None:
                if c1 == 'on' or c1 == '1':
                    print("VM instruction execution logging is now enabled")
                    settings.set_log_vm_instruction(True)
                if c1 == 'off' or c1 == '0':
                    print("VM instruction execution logging is now disabled")
                    settings.set_log_vm_instruction(False)

            else:
                print("Cannot configure VM instruction logging. Please specify on|off")

        else:
            print("Cannot configure %s try 'config sc-events on|off', 'config debug on|off', 'config sc-debug-notify on|off' or 'config vm-log on|off'" % what)

    def run(self):
        dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
        dbloop.start(.1)

        Blockchain.Default().PersistBlocks()

        tokens = [(Token.Neo, 'NEO'), (Token.Default, ' cli. Type '),
                  (Token.Command, '\'help\' '), (Token.Default, 'to get started')]

        print_tokens(tokens, self.token_style)
        print('\n')

        while self.go_on:

            try:
                result = prompt("neo> ",
                                completer=self.get_completer(),
                                history=self.history,
                                get_bottom_toolbar_tokens=self.get_bottom_toolbar,
                                style=self.token_style,
                                refresh_interval=3
                                )
            except EOFError:
                # Control-D pressed: quit
                return self.quit()
            except KeyboardInterrupt:
                # Control-C pressed: do nothing
                continue

            try:
                command, arguments = self.input_parser.parse_input(result)

                if command is not None and len(command) > 0:
                    command = command.lower()

                    if command == 'quit' or command == 'exit':
                        self.quit()
                    elif command == 'help':
                        self.help()
                    elif command == 'create':
                        self.do_create(arguments)
                    elif command == 'open':
                        self.do_open(arguments)
                    elif command == 'build':
                        self.do_build(arguments)
                    elif command == 'load_run':
                        self.do_load_n_run(arguments)
                    elif command == 'import':
                        self.do_import(arguments)
                    elif command == 'export':
                        self.do_export(arguments)
                    elif command == 'wallet':
                        self.show_wallet(arguments)
                    elif command == 'send':
                        self.do_send(arguments)
                    elif command == 'sign':
                        self.do_sign(arguments)
                    elif command == 'block':
                        self.show_block(arguments)
                    elif command == 'tx':
                        self.show_tx(arguments)
                    elif command == 'header':
                        self.show_header(arguments)
                    elif command == 'account':
                        self.show_account_state(arguments)
                    elif command == 'asset':
                        self.show_asset_state(arguments)
                    elif command == 'contract':
                        self.show_contract_state(arguments)
                    elif command == 'testinvoke':
                        self.test_invoke_contract(arguments)
                    elif command == 'withdraw_request':
                        self.make_withdraw_request(arguments)
                    elif command == 'withdraw':
                        self.do_withdraw(arguments)
                    elif command == 'notifications':
                        self.do_notifications(arguments)
                    elif command == 'mem':
                        self.show_mem()
                    elif command == 'nodes' or command == 'node':
                        self.show_nodes()
                    elif command == 'state':
                        self.show_state()
                    elif command == 'debugstorage':
                        self.handle_debug_storage(arguments)
                    elif command == 'config':
                        self.configure(arguments)
                    elif command is None:
                        print("Please specify a command")
                    else:
                        print("Command %s not found" % command)

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

    # Show the neo-python version
    parser.add_argument("--version", action="version",
                        version="neo-python v{version}".format(version=__version__))

    args = parser.parse_args()

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

    if args.theme:
        preferences.set_theme(args.theme)

    if args.verbose:
        settings.set_log_smart_contract_events(True)

    if args.datadir:
        settings.set_data_dir(args.datadir)

    # Instantiate the blockchain and subscribe to notifications
    blockchain = LevelDBBlockchain(settings.chain_leveldb_path)
    Blockchain.RegisterBlockchain(blockchain)

    # Try to set up a notification db
    if NotificationDB.instance():
        NotificationDB.instance().start()

    # Start the prompt interface
    cli = PromptInterface()

    # Run things
    reactor.suggestThreadPoolSize(15)
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
