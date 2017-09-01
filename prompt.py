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
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo import Settings
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

    completer = WordCompleter(['block','tx','header','mem','help','state','node','exit','quit','config','db','log'])

    _gathering_password = False
    _gathered_passwords = []
    _gather_password_action = None
    _gather_address_str = None
    _num_passwords_req = 0
    _wallet_create_path = None


    Wallet = None

    commands = ['quit',
                'help',
                'block {index/hash}',
                'header {index/hash}',
                'tx {hash}',
                'mem',
                'nodes',
                'state',
                'config {node, db} int int'
                'config log on/off'
                'pause',
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

    node_leader = None

    paused = False

    def paused_loop(self):

        while self.paused:
#            self.__log.debug("paused...")
            time.sleep(1)

    def get_bottom_toolbar(self, cli=None):
        try:
            return [(Token.Command, 'Progress: '),
                    (Token.Number, str(Blockchain.Default().Height)),
                    (Token.Neo, '/'),
                    (Token.Number, str(Blockchain.Default().HeaderHeight))]
        except Exception as e:
            print("couldnt get toolbar: %s " % e)
            return []


    def quit(self):
        print('Shutting down.  This may take a bit...')
        self.go_on = False
        self.paused = False
        Blockchain.Default().Dispose()
        reactor.stop()
        self.node_leader.Shutdown()

    def help(self):
        tokens = []
        for c in self.commands:
            tokens.append((Token.Command, "%s\n" %c))
        print_tokens(tokens, self.token_style)

    def toggle_pause(self):
        if self.paused:
            self.paused = not self.paused
#            reactor.run()
            print("resusiming execution")

        else:
            self.paused = not self.paused
            print('pausing execution!')
            reactor.callLater(1,self.paused_loop)


    def do_open(self, arguments):
        item = self.get_arg(arguments)

        if item and item == 'wallet':

            path = self.get_arg(arguments, 1)

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
        item = self.get_arg(arguments)

        if item and item == 'wallet':

            path = self.get_arg(arguments, 1)

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

        contracts = self.Wallet.GetContracts()
        contract = contracts[ list(contracts.keys())[0]]
        key = self.Wallet.GetKey(contract.PublicKeyHash.ToBytes())

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
            print("could not open wallet %s " % e)
            traceback.print_stack()
            traceback.print_exc()


    def do_import(self, arguments):
        item = self.get_arg(arguments)

        if item and item == 'wif':

            if not self.Wallet:
                print("Please open a wallet before importing WIF")
                return

            wif = self.get_arg(arguments, 1)

            if wif:
                print("import wif not implemented yet")
                return
            else:
                print("Please specify a wif")
                return

        print("please specify something to import")
        return




    def do_export(self, arguments):
        item = self.get_arg(arguments)

        if item == 'wif':

            if not self.Wallet:
                print("please open a wallet")
                return
            addr = self.get_arg(arguments, 1)

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

        print("exporting wif for address %s" % (address))
        


    def show_wallet(self, arguments):


        if not self.Wallet:
            print("please open a wallet")
            return

        item = self.get_arg(arguments)

        if not item:
            print("Wallet %s " % json.dumps(self.Wallet.ToJson(), indent=4))

        if item == 'rebuild':
            self.Wallet.Rebuild()
            try:
                item2 = int(self.get_arg(arguments,1))
                if item2 and item2 > 0:
                    print('restarting at %s ' % item2)
                    self.Wallet._current_height = item2
            except Exception as e:
                pass
        if item == 'unspent':
            self.Wallet.FindUnspentCoins()

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
        if self.node_leader and len(self.node_leader.Peers):
            out = ''
            for peer in self.node_leader.Peers:
                out+='Peer %s - IO: %s\n' % (peer.Name(), peer.IOStats())
            print_tokens([(Token.Number, out)], self.token_style)
        else:
            print('Not connected yet\n')


    def show_block(self, args):
        item = self.get_arg(args)
        txarg = self.get_arg(args, 1)
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
        item = self.get_arg(args)
        if item is not None:
            header = Blockchain.Default().GetHeaderBy(item)
            if header is not None:
                print(json.dumps(header.ToJson(), indent=4))
            else:
                print("could not locate Header %s \n" % item)
        else:
            print("please specify a header")


    def show_tx(self, args):
        item = self.get_arg(args)
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
        item = self.get_arg(args)
        print("account to show %s " % item)

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
        item = self.get_arg(args)
        print("asset to show %s " % item)

        if item is not None:
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
        item = self.get_arg(args)

        if item is not None:

            if item.lower() == 'all':
                contracts = Blockchain.Default().ShowAllContracts()
                print("contracts: %s " % contracts)
            else:
                contract = Blockchain.Default().GetContract(item)
                if contract is not None:
                    bjson = json.dumps(contract.ToJson(), indent=4)
                    tokens = [(Token.Number, bjson)]
                    print_tokens(tokens, self.token_style)
                    print('\n')
        else:
            print("please specify a contract")

    def show_spent_coins(self, args):
        item = self.get_arg(args)

        if item is not None:
            if item.lower() == 'all':
                coins = Blockchain.Default().GetAllSpentCoins()
                print("coins %s " % coins)
            else:

                coin = Blockchain.Default().GetSpentCoins(item)
                if coin is not None:
                    bjson = json.dumps(coin.ToJson(), indent=4)
                    tokens = [(Token.Number, bjson)]
                    print_tokens(tokens, self.token_style)
                    print("\n")
        else:
            print("please specify a tx hash")

    def show_mem(self):
        total = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        totalmb = total / 1000000
        out = "Total: %s MB\n" % totalmb
        out += "total buffers %s\n" % StreamManager.TotalBuffers()
        print_tokens([(Token.Number, out)], self.token_style)

    def configure(self, args):
        what = self.get_arg(args)

        if what == 'node':
            c1 = self.get_arg(args,1, convert_to_int=True)
            c2 = self.get_arg(args, 2, convert_to_int=True)

            if not c1:
                print("please provide settings. arguments must be integers")

            if c1 is not None and c1 > 1:
                if c1 > 200:
                    c1 = 200
                    print("Node request part must be less than 201")
                self.node_leader.BREQPART = c1
                print("Set Node Request Part to %s " % c1)
            if c2 is not None and c2 >= self.node_leader.BREQPART:
                self.node_leader.BREQMAX = c2
                print("Set Node Request Max to %s " % c2)
            self.show_state()
        elif what == 'db':
            c1 = self.get_arg(args, 1, convert_to_int=True)
            c2 = self.get_arg(args, 2, convert_to_int=True)
            if c1 is not None and c1 > 1:
                Blockchain.Default().CACHELIM = c1
                print("Set DB Cache Limit to %s " % c1)
            if c2 is not None and c2 >= self.node_leader.BREQPART:
                Blockchain.Default().CMISSLIM = c2
                print("Set DB Cache Miss Limit %s " % c2)
            self.show_state()
        elif what =='log' or what == 'logs':
            c1 = self.get_arg(args, 1).lower()
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
            print("Try 'config node 100 1000' or config db 1000 4' or config log on/off")

    def get_arg(self, arguments, index=0, convert_to_int=False):
        try:
            arg = arguments[index]
            if convert_to_int:
                return int(arg)
            return arg
        except Exception as e:
            pass
        return None


    def parse_result(self, result):
        if len(result):
            commandParts = [s for s in result.split()]
            return commandParts[0], commandParts[1:]
        return None,None

    def run(self):

        dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
        dbloop.start(.1)

        Blockchain.Default().PersistBlocks()

        self.node_leader = NodeLeader.Instance()

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
                    elif command == 'block':
                        self.show_block(arguments)
                    elif command == 'tx':
                        self.show_tx(arguments)
                    elif command == 'header':
                        self.show_header(arguments)
                    elif command =='account':
                        self.show_account_state(arguments)
                    elif command == 'asset':
                        self.show_asset_state(arguments)
                    elif command =='contract':
                        self.show_contract_state(arguments)
                    elif command == 'sc':
                        self.show_spent_coins(arguments)
                    elif command == 'mem':
                        self.show_mem()
                    elif command == 'nodes' or command == 'node':
                        self.show_nodes()
                    elif command == 'state':
                        self.show_state()
                    elif command == 'config':
                        self.configure(arguments)
                    elif command == 'pause' or command == 'unpause' or command == 'resume':
                        self.toggle_pause()
                    elif command == None:
                        print('please specify a command')
                    else:
                        print("command %s not found" % command)

                else:
                    pass


if __name__ == "__main__":

    cli = PromptInterface()

#    reactor.suggestThreadPoolSize(15)
    reactor.callInThread(cli.run)
    NodeLeader.Instance().Start()
    reactor.run()
