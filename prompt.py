#!/usr/bin/env python


"""

"""

import json
import logging
import datetime
import math
import time
import gc
from neo.IO.MemoryStream import StreamManager
from neo.Network.NodeLeader import NodeLeader

import resource

from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo import Settings


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
                ]

    token_style = style_from_dict({
        Token.Command: '#ff0066',
        Token.Neo: '#0000ee',
        Token.Default: '#00ee00',
        Token.Number: "#ffffff",
    })

    history = InMemoryHistory()

    start_height = Blockchain.Default().Height()
    start_dt = datetime.datetime.utcnow()

    node_leader = None

    def get_bottom_toolbar(self, cli=None):
        try:
            return [(Token.Command, 'Progress: '),
                    (Token.Number, str(Blockchain.Default().Height())),
                    (Token.Neo, '/'),
                    (Token.Number, str(Blockchain.Default().HeaderHeight()))]
        except Exception as e:
            print("couldnt get toolbar: %s " % e)
            return []


    def quit(self):
        print('Shutting down.  This may take a bit...')
        self.go_on = False
        #Blockchain.Default().Dispose()
        reactor.stop()
        self.node_leader.Shutdown()

    def help(self):
        tokens = []
        for c in self.commands:
            tokens.append((Token.Command, "%s\n" %c))
        print_tokens(tokens, self.token_style)


    def show_state(self):
        height = Blockchain.Default().Height()
        headers = Blockchain.Default().HeaderHeight()

        diff = height - self.start_height
        now = datetime.datetime.utcnow()
        difftime = now - self.start_dt

        mins = difftime / datetime.timedelta(minutes=1)

        bpm = 0
        if diff > 0 and mins > 0:
            bpm = diff / mins

        out = 'Progress: %s / %s\n' % (height, headers)
        out += 'Block Cache length %s\n' % Blockchain.Default().BlockCacheCount()
        out += 'Blocks since program start %s\n' % diff
        out += 'Time elapsed %s mins\n' % mins
        out += 'blocks per min %s \n' % bpm
        out += "Node Req Part, Max: %s %s\n" % (self.node_leader.BREQPART, self.node_leader.BREQMAX)
        out += "DB Cache Lim, Miss Lim %s %s\n" % (Blockchain.Default().CACHELIM, Blockchain.Default().CMISSLIM)
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
            tx,height = Blockchain.Default().GetTransaction(item)
            if height  > -1:

                bjson = json.dumps(tx.ToJson(), indent=4)
                tokens = [(Token.Command, bjson)]
                print_tokens(tokens, self.token_style)
                print('\n')

            else:
                print("tx %s not found" % item)
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
            commandParts = [s.lower() for s in result.split()]
            return commandParts[0], commandParts[1:]
        return None,None

    def run(self):

        dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
        dbloop.start(.02)

        self.node_leader = NodeLeader.Instance()

        tokens = [(Token.Neo, 'NEO'),(Token.Default,' cli. Type '),(Token.Command, "'help' "), (Token.Default, 'to get started')]
        print_tokens(tokens, self.token_style)
        print("\n")

        while self.go_on:

            result = prompt("neo> ",
                            completer=self.completer,
                            history=self.history,
                            get_bottom_toolbar_tokens=self.get_bottom_toolbar,
                            style=self.token_style)

            command, arguments = self.parse_result(result)
            if command == 'quit' or command == 'exit':
                self.quit()
            elif command == 'help':
                self.help()
            elif command == 'block':
                self.show_block(arguments)
            elif command == 'tx':
                self.show_tx(arguments)
            elif command == 'header':
                self.show_header(arguments)
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





if __name__ == "__main__":

    cli = PromptInterface()

    reactor.suggestThreadPoolSize(10)
    reactor.callInThread(cli.run)
    NodeLeader.Instance().Start()
    reactor.run()
