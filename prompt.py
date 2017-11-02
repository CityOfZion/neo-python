#!/usr/bin/env python


import json
import logging
import datetime
import os
import argparse
from neo.IO.MemoryStream import StreamManager
import resource

from neo.Core.Blockchain import Blockchain
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Wallets.KeyPair import KeyPair
from neo.Network.NodeLeader import NodeLeader
from neo.Prompt.Commands.Invoke import InvokeContract,TestInvokeContract,test_invoke,InvokeWithdrawTx
from neo.Prompt.Commands.BuildNRun import BuildAndRun,LoadAndRun
from neo.Prompt.Commands.Withdraw import RequestWithdraw,RedeemWithdraw
from neo.Prompt.Commands.LoadSmartContract import LoadContract,GatherContractDetails,ImportContractAddr,ImportMultiSigContractAddr
from neo.Prompt.Commands.Send import construct_and_send,construct_contract_withdrawal,parse_and_sign
from neo.Prompt.Commands.Wallet import DeleteAddress,ImportWatchAddr
from neo.Prompt.Utils import get_arg
from neo.Prompt.Notify import SubscribeNotifications
from neo.Settings import settings
from neo.Fixed8 import Fixed8
from neo.UInt160 import UInt160
from neo.UInt256 import UInt256
import traceback

from twisted.internet import reactor, task

from autologging import logged

from prompt_toolkit import prompt
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.shortcuts import print_tokens
from prompt_toolkit.token import Token
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.history import FileHistory

debug_logname = 'prompt.log'

logging.basicConfig(
     level=logging.DEBUG,
     filemode='a',
     filename=debug_logname,
     format="%(asctime)s %(levelname)s:%(name)s:%(funcName)s:%(message)s")




import csv

example_style = style_from_dict({
    # User input.
    Token:          '#ff0066',

    # Prompt.
    Token.Username: '#884444',
    Token.At:       '#00aa00',
    Token.Colon:    '#00aa00',
    Token.Pound:    '#00aa00',
    Token.Host:     '#000088 bg:#aaaaff',
    Token.Path:     '#884444 underline',
})


@logged
class PromptInterface(object):


    go_on = True


    _gathering_password = False
    _gathered_passwords = []
    _gather_password_action = None
    _gather_address_str = None
    _num_passwords_req = 0
    _wallet_create_path = None
    _wallet_send_tx = None

    _invoke_test_tx = None
    _invoke_test_tx_fee = None

    _walletdb_loop = None

    Wallet = None

    _known_addresses = []

    commands = ['quit',
                'help',
                'block {index/hash} (tx)',
                'header {index/hash}',
                'tx {hash}',
                'asset {assetId}',
                'asset search {query}',
                'contract {contract hash}',
                'contract search {query}',
                'mem',
                'nodes',
                'state',
                'config log {on/off}',
                'build {path/to/file.py} (test {params} {returntype} {needs_storage} {test_params})',
                'import wif {wif}',
                'import contract {path/to/file.avm} {params} {returntype} {needs_storage}',
                'import contract_addr {contract_hash} {pubkey}',
                'import watch_addr {address}',
                'export wif {address}',
                'open wallet {path}',
                'create wallet {path}',
                'wallet {verbose}',
                'wallet migrate',
                'wallet rebuild {start block}',
                'wallet delete_addr {addr}',
                'wallet close',
                'send {assetId or name} {address} {amount} (--from-addr={addr})',
                'sign {transaction in JSON format}',
                'testinvoke {contract hash} {params} (--attach-neo={amount}, --attach-gas={amount)',
                'invoke',
                'cancel',
                ]

    token_style = style_from_dict({
        Token.Command: '#ff0066',
        Token.Neo: '#0000ee',
        Token.Default: '#00ee00',
        Token.Number: "#ffffff",
    })

    history = FileHistory('.prompt.py.history')

    start_height = None
    start_dt = None

    def __init__(self):
        self.start_height = Blockchain.Default().Height
        self.start_dt = datetime.datetime.utcnow()


    def get_bottom_toolbar(self, cli=None):
        out = []
        try:
            out =[(Token.Command, '[%s] Progress: ' % settings.net_name),
                    (Token.Number, str(Blockchain.Default().Height)),
                    (Token.Neo, '/'),
                    (Token.Number, str(Blockchain.Default().HeaderHeight))]
        except Exception as e:
            pass

        return out


    def get_completer(self):
        standard_completions = ['block', 'tx', 'header', 'mem', 'neo','gas',
                                    'help', 'state', 'node', 'exit', 'quit',
                                    'config', 'import', 'export', 'open',
                                    'wallet', 'contract', 'asset', 'wif',
                                    'withdraw_request','withdraw',
                                    'watch_addr','contract_addr', 'testinvoke',]

        if self.Wallet:
            for addr in self.Wallet.Addresses:
                if not addr in self._known_addresses:
                    self._known_addresses.append(addr)

        all_completions = standard_completions + self._known_addresses

        completer = WordCompleter(all_completions)

        return completer

    def quit(self):
        print('Shutting down.  This may take a bit...')
        self.go_on = False
        Blockchain.Default().Dispose()
        reactor.stop()
        NodeLeader.Instance().Shutdown()

    def help(self):
        tokens = []
        for c in self.commands:
            tokens.append((Token.Command, "%s\n" %c))
        print_tokens(tokens, self.token_style)

    def do_open(self, arguments):

        if self.Wallet:
            self.do_close_wallet()


        item = get_arg(arguments)

        if item and item == 'wallet':

            path = get_arg(arguments, 1)

            if path:

                if not os.path.exists(path):
                    print("wallet file not found")
                    return


                self._num_passwords_req = 1
                self._wallet_create_path = path
                self._gathered_passwords = []
                self._gathering_password = True
                self._gather_password_action = self.do_open_wallet
            else:
                print("Please specify a path")
        else:
            print("item is? %s " % item)

    def do_create(self, arguments):
        item = get_arg(arguments)

        if item and item == 'wallet':

            path = get_arg(arguments, 1)

            if path:

                if os.path.exists(path):
                    print("File already exists")
                    return

                self._num_passwords_req = 2
                self._wallet_create_path = path
                self._gathered_passwords = []
                self._gathering_password = True
                self._gather_password_action = self.do_create_wallet
     #           print("create wallet! Please specify a password")
            else:
                print("Please specify a path")





    def do_create_wallet(self):
#        print("do create wallet with passwords %s "% self._gathered_passwords)

        if self.Wallet:
            self.do_close_wallet()

        psswds = self._gathered_passwords
        path = self._wallet_create_path
        self._wallet_create_path = None
        self._gathered_passwords = None
        self._gather_password_action = None

        if len(psswds) != 2 or psswds[0] != psswds[1] or len(psswds[0]) < 10:
            print("please provide matching passwords that are at least 10 characters long")
            return

        passwd = psswds[1]

        try:
            self.Wallet = UserWallet.Create(path=path , password=passwd)
        except Exception as e:
            print("Exception creating wallet: %s " % e)

        contract = self.Wallet.GetDefaultContract()
        key = self.Wallet.GetKey(contract.PublicKeyHash)

        print("Wallet %s " % json.dumps(self.Wallet.ToJson(), indent=4))
        print("pubkey %s " % key.PublicKey.encode_point(True))


        self._walletdb_loop = task.LoopingCall(self.Wallet.ProcessBlocks)
        self._walletdb_loop.start(1)


    def do_close_wallet(self):
        if self.Wallet:
            path = self.Wallet._path
            self._walletdb_loop.stop()
            self._walletdb_loop = None
            self.Wallet = None
            print("closed wallet %s " % path)

    def do_open_wallet(self):


        passwd = self._gathered_passwords[0]
        path = self._wallet_create_path
        self._wallet_create_path = None
        self._gathered_passwords = None
        self._gather_password_action = None

        try:
            self.Wallet = UserWallet.Open(path, passwd)

            self._walletdb_loop = task.LoopingCall(self.Wallet.ProcessBlocks)
            self._walletdb_loop.start(1)
            print("Opened wallet at %s" % path)
        except Exception as e:
            print("could not open wallet: %s " % e)
#            traceback.print_stack()
#            traceback.print_exc()


    def do_import(self, arguments):
        item = get_arg(arguments)

        if item:

            if item == 'wif':

                if not self.Wallet:
                    print("Please open a wallet before importing WIF")
                    return

                wif = get_arg(arguments, 1)

                if wif:
                    prikey = KeyPair.PrivateKeyFromWIF(wif)
                    if prikey:

                        key = self.Wallet.CreateKey(prikey)
                        print("imported key %s " % wif)
                        print("Pubkey: %s \n" % key.PublicKey.encode_point(True).hex())
                        print("Wallet: %s " % json.dumps(self.Wallet.ToJson(), indent=4))
                    else:
                        print("invalid wif")
                    return

            elif item == 'contract':
                return self.load_smart_contract(arguments)


            elif item == 'contract_addr':
                return ImportContractAddr(self.Wallet, arguments[1:])

            elif item == 'watch_addr':
                return ImportWatchAddr(self.Wallet, get_arg(arguments,1))

            elif item == 'multisig_addr':
                return ImportMultiSigContractAddr(self.Wallet, arguments[1:])



        print("please specify something to import")
        return

    def do_build(self, arguments):
        BuildAndRun(arguments, self.Wallet)

    def do_load_n_run(self, arguments):
        LoadAndRun(arguments, self.Wallet)

    def do_export(self, arguments):
        item = get_arg(arguments)

        if item == 'wif':

            if not self.Wallet:
                print("please open a wallet")
                return
            addr = get_arg(arguments, 1)

            if not addr:
                print('please specify an address')
                return

            if not self.Wallet.ContainsAddressStr(addr):
                print("address %s not found in wallet" % addr)
                return

            self._num_passwords_req = 1
            self._gather_address_str = addr
            self._gathered_passwords = []
            self._gathering_password = True
            self._gather_password_action = self.do_export_wif
            return

        print("Command export %s not found" % item)

    def do_export_wif(self):
        passwd = self._gathered_passwords[0]
        address = self._gather_address_str
        self._gather_address_str = None
        self._gathered_passwords = None
        self._gather_password_action = None

        if not self.Wallet.ValidatePassword(passwd):
            print("incorrect password")
            return


        keys = self.Wallet.GetKeys()
        for key in keys:
            export = key.Export()
            print("key export : %s " % export)


    def show_wallet(self, arguments):


        if not self.Wallet:
            print("please open a wallet")
            return

        item = get_arg(arguments)

        if not item:
            print("Wallet %s " % json.dumps(self.Wallet.ToJson(), indent=4))
            return

        if item in ['v','--v','verbose']:
            print("Wallet %s " % json.dumps(self.Wallet.ToJson(verbose=True), indent=4))
            return

        if item == 'migrate' and self.Wallet is not None:
            print("migrating wallet...")
            self.Wallet.Migrate()
            print("migrated wallet")

        if item == 'delete_addr':
            addr_to_delete = get_arg(arguments, 1)
            DeleteAddress(self, self.Wallet, addr_to_delete)

        if item == 'close':
            self.do_close_wallet()

        if item == 'rebuild':
            self.Wallet.Rebuild()
            try:
                item2 = int(get_arg(arguments,1))
                if item2 and item2 > 0:
                    print('restarting at %s ' % item2)
                    self.Wallet._current_height = item2
            except Exception as e:
                pass
        if item == 'unspent':
            self.Wallet.FindUnspentCoins()

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

        out = 'Progress: %s / %s\n' % (height, headers)
        out += 'Block Cache length %s\n' % Blockchain.Default().BlockCacheCount
        out += 'Blocks since program start %s\n' % diff
        out += 'Time elapsed %s mins\n' % mins
        out += 'blocks per min %s \n' % bpm
        tokens = [(Token.Number, out)]
        print_tokens(tokens, self.token_style)

    def show_nodes(self):
        if len( NodeLeader.Instance().Peers) > 0:
            out = ''
            for peer in NodeLeader.Instance().Peers:
                out+='Peer %s - IO: %s\n' % (peer.Name(), peer.IOStats())
            print_tokens([(Token.Number, out)], self.token_style)
        else:
            print('Not connected yet\n')


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
                print("could not locate block %s" % item)
        else:
            print("please specify a block")

    def show_header(self, args):
        item = get_arg(args)
        if item is not None:
            header = Blockchain.Default().GetHeaderBy(item)
            if header is not None:
                print(json.dumps(header.ToJson(), indent=4))
            else:
                print("could not locate Header %s \n" % item)
        else:
            print("please specify a header")


    def show_tx(self, args):
        item = get_arg(args)
        if item is not None:
            try:
                tx,height = Blockchain.Default().GetTransaction(item)
                if height  > -1:

                    bjson = json.dumps(tx.ToJson(), indent=4)
                    tokens = [(Token.Command, bjson)]
                    print_tokens(tokens, self.token_style)
                    print('\n')
            except Exception as e:
                print("Could not find transaction with id %s " % item)
                print("Please specify a tx hash like 'db55b4d97cf99db6826967ef4318c2993852dff3e79ec446103f141c716227f6'")
        else:
            print("please specify a tx hash")


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
                print("account %s not found" % item)
        else:
            print("please specify an account address")

    def show_asset_state(self, args):
        item = get_arg(args)

        if item is not None:

            if item == 'search':
                query = get_arg(args, 1)
                results = Blockchain.Default().SearchAssetState(query)
                print("Found %s results for %s " % (len(results), query))
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
                print("asset %s not found" % item)
        else:
            print("please specify an asset hash")

    def show_contract_state(self, args):
        item = get_arg(args)

        if item is not None:

            if item.lower() == 'all':
                contracts = Blockchain.Default().ShowAllContracts()
                print("contracts: %s " % contracts)
            elif item.lower() == 'search':
                query = get_arg(args, 1)
                if query:

                    contracts = Blockchain.Default().SearchContracts(query=query)
                    print("Found %s results for %s " % (len(contracts), query))
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
                    bjson = json.dumps(contract.ToJson(), indent=4)
                    tokens = [(Token.Number, bjson)]
                    print_tokens(tokens, self.token_style)
                    print('\n')
        else:
            print("please specify a contract")


    def load_smart_contract(self, args):

        if not self.Wallet:
            print("please open wallet")
            return

        function_code = LoadContract(args[1:])

        if function_code:


            contract_script = GatherContractDetails(function_code, self)

            if contract_script is not None:

                tx, fee, results, num_ops = test_invoke(contract_script, self.Wallet, [])

                if tx is not None and results is not None:
                    self._invoke_test_tx = tx
                    self._invoke_test_tx_fee = fee
                    print("\n-------------------------------------------------------------------------------------------------------------------------------------")
                    print("Test deploy invoke successful")
                    print("Total operations executed: %s " % num_ops)
                    print("Results %s " % [str(item) for item in results])
                    print("Deploy Invoke TX gas cost: %s " % (tx.Gas.value / Fixed8.D))
                    print("Deploy Invoke TX Fee: %s " % (fee.value / Fixed8.D))
                    print("-------------------------------------------------------------------------------------------------------------------------------------\n")
                    print("You may now deploy this contract on the blockchain by using the 'invoke' command with no arguments or type 'cancel' to cancel deploy\n")
                    return
                else:
                    print("test ivoke failed")
                    print("tx is, results are %s %s " % (tx, results))
                    return


    def do_request_withdraw(self, args):
        """
        withdraw_request {CONTRACT_ADDR} {ASSET} {TO_ADDR} {AMOUNT}
        """

        RequestWithdraw(self, self.Wallet, args)

    def do_withdraw_from(self, args):
        """
        withdraw {CONTRACT_ADDR} {ASSET} {TO_ADDR} {AMOUNT}
        """

        RedeemWithdraw(self, self.Wallet, args)



    def test_invoke_contract(self, args):
        self._invoke_test_tx = None
        self._invoke_test_tx_fee = None

        if not self.Wallet:
            print("please open a wallet")
            return


        if args and len(args) > 0:
            tx, fee, results,num_ops = TestInvokeContract(self.Wallet, args)

            if tx is not None and results is not None:
                self._invoke_test_tx = tx
                self._invoke_test_tx_fee = fee
                print("\n-------------------------------------------------------------------------------------------------------------------------------------")
                print("Test invoke successful")
                print("Total operations: %s " % num_ops)
                print("Results %s " % [str(item) for item in results])
                print("Invoke TX gas cost: %s " % (tx.Gas.value / Fixed8.D))
                print("Invoke TX Fee: %s " % (fee.value / Fixed8.D))
                print("-------------------------------------------------------------------------------------------------------------------------------------\n")
                print("You may now invoke this on the blockchain by using the 'invoke' command with no arguments or type 'cancel' to cancel invoke\n")
                return
            else:
                print("Error testing contract invoke")
                return

        print("please specify a contract to invoke")

    def invoke_contract(self, args):

        if not self._invoke_test_tx:
            print("Please test your invoke before deploying it with the 'testinvoke {contracthash} *args' command")
            return

        result = InvokeContract(self.Wallet, self._invoke_test_tx, self._invoke_test_tx_fee)

        self._invoke_test_tx = None
        self._invoke_test_tx_fee = None
        return

    def cancel_operations(self):
        self._invoke_test_tx = None
        self._invoke_test_tx_fee = None
        self._invoke_withdraw_tx_fee = None
        self._invoke_withdraw_tx = None
        print("Operation cancelled")
        return


    def show_mem(self):
        total = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        totalmb = total / 1000000
        out = "Total: %s MB\n" % totalmb
        out += "total buffers %s\n" % StreamManager.TotalBuffers()
        print_tokens([(Token.Number, out)], self.token_style)

    def configure(self, args):
        what = get_arg(args)

        if what =='log' or what == 'logs':
            c1 = get_arg(args, 1).lower()
            if c1 is not None:
                if c1 == 'on' or c1 =='1':
                    print("turning on logging")
                    logger = logging.getLogger()
                    logger.setLevel(logging.DEBUG)
                if c1 == 'off' or c1 == '0':
                    print("turning off logging")
                    logger = logging.getLogger()
                    logger.setLevel(logging.ERROR)

            else:
                print("cannot configure log.  Please specify on or off")
        else:
            print("cannot configure %s " % what)
            print("Try 'config log on/off'")


    def parse_result(self, result):
        if len(result):
            commandParts = [s for s in result.split()]
            return commandParts[0], commandParts[1:]
        return None,None

    def run(self):

        dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
        dbloop.start(.1)

        Blockchain.Default().PersistBlocks()

        tokens = [(Token.Neo, 'NEO'),(Token.Default,' cli. Type '),(Token.Command, "'help' "), (Token.Default, 'to get started')]
        print_tokens(tokens, self.token_style)
        print("\n")

        while self.go_on:


            if self._gathered_passwords and len(self._gathered_passwords) == self._num_passwords_req:
                self._gathering_password = False
                self._gather_password_action()

            if self._gathering_password:
                result = prompt("password> ", is_password=True)

            else:
                try:
                    result = prompt("neo> ",
                                    completer=self.get_completer(),
                                    history=self.history,
                                    get_bottom_toolbar_tokens=self.get_bottom_toolbar,
                                    style=self.token_style,
                                    refresh_interval=.5)
                except EOFError:
                    # Control-D pressed: quit
                    return self.quit()
                except KeyboardInterrupt:
                    # Control-C pressed: do nothing
                    continue


            if self._gathering_password:
                self._gathered_passwords.append(result)

            else:

                try:
                    command, arguments = self.parse_result(result)

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
                        elif command == 'invoke':
                            self.invoke_contract(arguments)
                        elif command == 'testinvoke':
                            self.test_invoke_contract(arguments)
                        elif command == 'withdraw_request':
                            self.do_request_withdraw(arguments)
                        elif command == 'withdraw':
                            self.do_withdraw_from(arguments)
                        elif command == 'cancel':
                            self.cancel_operations()
                        elif command == 'mem':
                            self.show_mem()
                        elif command == 'nodes' or command == 'node':
                            self.show_nodes()
                        elif command == 'state':
                            self.show_state()
                        elif command == 'config':
                            self.configure(arguments)
                        elif command == None:
                            print('please specify a command')
                        else:
                            print("command %s not found" % command)

                except Exception as e:

                    print("could not execute command: %s " % e)
                    traceback.print_stack()
                    traceback.print_exc()



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mainnet", action="store_true", default=False, help="use MainNet instead of the default TestNet")
    parser.add_argument("-c", "--config", action="store", help="Use a specific config file")
    args = parser.parse_args()

    if args.mainnet and args.config:
        print("Cannot use bot --config and --mainnet parameters, please use only one.")
        exit(1)

    # Setup depending on command line arguments. By default, the testnet settings are already loaded.
    if args.config:
        settings.setup(args.config)
    elif args.mainnet:
        settings.setup_mainnet()

    # Instantiate the blockchain and subscribe to notifications
    blockchain = LevelDBBlockchain(settings.LEVELDB_PATH)
    Blockchain.RegisterBlockchain(blockchain)
    SubscribeNotifications()

    # Start the prompt interface
    cli = PromptInterface()

    # Run
    reactor.suggestThreadPoolSize(15)
    reactor.callInThread(cli.run)
    NodeLeader.Instance().Start()
    reactor.run()
