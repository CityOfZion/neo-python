#!/usr/bin/env python


"""

"""

import json
import logging
import datetime
import time
import os
from neo.IO.MemoryStream import StreamManager
from neo.Network.NodeLeader import NodeLeader
import resource

from neo.Core.Blockchain import Blockchain
from neo.Core.TX.Transaction import Transaction,ContractTransaction,TransactionOutput
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neo.Wallets.KeyPair import KeyPair
from neo.Network.NodeLeader import NodeLeader
from neo.Prompt.Commands.Invoke import InvokeContract,TestInvokeContract,test_invoke,test_deploy_and_invoke
from neo.Prompt.Commands.LoadSmartContract import LoadContract,GatherContractDetails,GatherLoadedContractParams
from neo.Prompt.Utils import get_arg
from neo.Prompt.Notify import SubscribeNotifications
from neo import Settings
from neo.Fixed8 import Fixed8
import traceback

from twisted.internet import reactor, task

from autologging import logged

from prompt_toolkit import prompt
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.shortcuts import print_tokens
from prompt_toolkit.token import Token
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.history import InMemoryHistory


logname = 'prompt.log'
logging.basicConfig(
     level=logging.DEBUG,
     filemode='a',
     filename=logname,
     format="%(levelname)s:%(name)s:%(funcName)s:%(message)s")

blockchain = LevelDBBlockchain(Settings.LEVELDB_PATH)
Blockchain.RegisterBlockchain(blockchain)
SubscribeNotifications()


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

    completer = WordCompleter(['block','tx','header','mem',
                               'help','state','node','exit','quit',
                               'config', 'import','export','open',
                               'wallet','contract','asset',])

    _gathering_password = False
    _gathered_passwords = []
    _gather_password_action = None
    _gather_address_str = None
    _num_passwords_req = 0
    _wallet_create_path = None
    _wallet_send_tx = None

    _invoke_test_tx = None
    _invoke_test_tx_fee = None

    Wallet = None

    commands = ['quit',
                'help',
                'block {index/hash}',
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
                'import wif {wif}',
                'import contract {path} {params} {returntype}',
                'export wif {address}'
                'open wallet {path}',
                'create wallet {path}',
                'wallet {verbose}',
                'wallet rebuild {start block}',
                'send {assetId or name} {address} {amount}',
                'testinvoke {contract hash} {params}',
                'invoke',
                'cancel',
                ]

    token_style = style_from_dict({
        Token.Command: '#ff0066',
        Token.Neo: '#0000ee',
        Token.Default: '#00ee00',
        Token.Number: "#ffffff",
    })

    history = InMemoryHistory()

    start_height = Blockchain.Default().Height
    start_dt = datetime.datetime.utcnow()


    def get_bottom_toolbar(self, cli=None):
        out = []
        try:
            out =[(Token.Command, 'Progress: '),
                    (Token.Number, str(Blockchain.Default().Height)),
                    (Token.Neo, '/'),
                    (Token.Number, str(Blockchain.Default().HeaderHeight))]
        except Exception as e:
            pass

        return out


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


        dbloop = task.LoopingCall(self.Wallet.ProcessBlocks)
        dbloop.start(1)


    def do_open_wallet(self):
        passwd = self._gathered_passwords[0]
        path = self._wallet_create_path
        self._wallet_create_path = None
        self._gathered_passwords = None
        self._gather_password_action = None

        try:
            self.Wallet = UserWallet.Open(path, passwd)

            dbloop = task.LoopingCall(self.Wallet.ProcessBlocks)
            dbloop.start(1)
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

            if item == 'contract':
                return self.load_smart_contract(arguments)

        print("please specify something to import")
        return


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

        if item == 'close':
            print('closed wallet')
            self.Wallet = None

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
        try:
            if not self.Wallet:
                print("please open a wallet")
                return
            if len(arguments) < 3:
                print("Not enough arguments")
                return

            to_send = get_arg(arguments)
            address = get_arg(arguments,1)
            amount = get_arg(arguments,2)

            assetId = None

            if to_send.lower() == 'neo':
                assetId = Blockchain.Default().SystemShare().Hash
            elif to_send.lower() == 'gas':
                assetId = Blockchain.Default().SystemCoin().Hash
            elif Blockchain.Default().GetAssetState(to_send):
                assetId = Blockchain.Default().GetAssetState(to_send).AssetId

            scripthash = self.Wallet.ToScriptHash(address)
            if scripthash is None:
                print("invalid address")
                return

            f8amount = Fixed8.TryParse(amount)
            if f8amount is None:
                print("invalid amount format")
                return

            if f8amount.value % pow(10, 8 - Blockchain.Default().GetAssetState(assetId.ToBytes()).Precision) != 0:
                print("incorrect amount precision")
                return

            fee = Fixed8.Zero()
            if get_arg(arguments,3):
                fee = Fixed8.TryParse(get_arg(arguments,3))

            output = TransactionOutput(AssetId=assetId,Value=f8amount,script_hash=scripthash)
            tx = ContractTransaction(outputs=[output])
            ttx = self.Wallet.MakeTransaction(tx=tx,change_address=None,fee=fee)


            if ttx is None:
                print("insufficient funds")
                return

            self._wallet_send_tx = ttx

            self._num_passwords_req = 1
            self._gathered_passwords = []
            self._gathering_password = True
            self._gather_password_action = self.do_send_created_tx


        except Exception as e:
            print("could not send: %s " % e)
            traceback.print_stack()
            traceback.print_exc()

    def do_send_created_tx(self):
        passwd = self._gathered_passwords[0]
        tx = self._wallet_send_tx
        self._wallet_send_tx = None
        self._gathered_passwords = None
        self._gather_password_action = None

        if not self.Wallet.ValidatePassword(passwd):
            print("incorrect password")
            return


        try:
            context = ContractParametersContext(tx)
            self.Wallet.Sign(context)

            if context.Completed:

                tx.scripts = context.GetScripts()

                self.Wallet.SaveTransaction(tx)

                relayed = NodeLeader.Instance().Relay(tx)

                if relayed:
                    print("Relayed Tx: %s " % tx.Hash.ToString())
                else:
                    print("Could not relay tx %s " % tx.Hash.ToString())


        except Exception as e:
            print("could not sign %s " % e)
            traceback.print_stack()
            traceback.print_exc()


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

                    for tx in block.Transactions:
                        self.show_tx([tx])


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

        if function_code is not None:


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
                result = prompt("neo> ",
                                completer=self.completer,
                                history=self.history,
                                get_bottom_toolbar_tokens=self.get_bottom_toolbar,
                                style=self.token_style)



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
                        elif command == 'import':
                            self.do_import(arguments)
                        elif command == 'export':
                            self.do_export(arguments)
                        elif command == 'wallet':
                            self.show_wallet(arguments)
                        elif command == 'send':
                            self.do_send(arguments)
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


if __name__ == "__main__":

    cli = PromptInterface()

    reactor.suggestThreadPoolSize(15)
    reactor.callInThread(cli.run)
    NodeLeader.Instance().Start()
    reactor.run()
