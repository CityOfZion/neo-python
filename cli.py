#!/usr/bin/env python

# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Example using stdio, Deferreds, LineReceiver and twisted.web.client.

Note that the WebCheckerCommandProtocol protocol could easily be used in e.g.
a telnet server instead; see the comments for details.

Based on an example by Abe Fettig.
"""

import pprint
import json
import logging
logname = 'cli.log'
logging.basicConfig(
     level=logging.DEBUG,
     filemode='a',
     filename=logname,
     format="%(levelname)s:%(name)s:%(funcName)s:%(message)s")



from neo.Network.NeoNode import NeoNode
from neo.Network.NeoNodeFactory import NeoFactory

from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo import Settings

blockchain = LevelDBBlockchain(Settings.LEVELDB_PATH)
Blockchain.RegisterBlockchain(blockchain)

from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
from twisted.internet import stdio, reactor, task
from twisted.protocols import basic
from twisted.web import client

from autologging import logged


@logged
class NeoCommandProtocol(basic.LineReceiver):
    delimiter = b'\n' # unix terminal style newlines. remove this line
                     # for use with Telnet

    server_running=False
    factory = None


    def send_line_to_b(self, value, and_ask_whats_next=False):

        if and_ask_whats_next:
            self.sendLine(b'%s     Ok.. what next?' % value.encode('utf-8'))
        else:
            self.sendLine(value.encode('utf-8'))

    def connectionMade(self):

        self.send_line_to_b('Starting Server... Please wait')

        dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
        dbloop.start(.1)


        #start up endpoints
        for bootstrap in Settings.SEED_LIST:
            host, port = bootstrap.split(":")
            point = TCP4ClientEndpoint(reactor, host, int(port))
            d = connectProtocol(point, NeoNode(NeoFactory))
            d.addCallbacks(self.onProtocolConnected, self.onProtocolError)



        self.send_line_to_b("Neo console. Type 'help' for help.")


    def lineReceived(self, line):
        # Ignore blank lines
        if not line: return

        # Parse the command
        line = line.decode('utf-8')
        commandParts = line.split()
        command = commandParts[0].lower()
        args = commandParts[1:]

        # Dispatch the command to the appropriate method.  Note that all you
        # need to do to implement a new command is add another do_* method.
        try:
            method = getattr(self, 'do_' + command)
        except AttributeError as e:
            self.send_line_to_b('Error: no such command.')
        else:
#            try:
            method(*args)
#if we catch exception here, its harder to debug
#            except Exception as e:
#                self.send_line_to_b('Error: ' + str(e))

    def do_help(self, command=None):
        """help [command]: List commands, or show help on the given command"""
        if command:
            self.send_line_to_b(getattr(self, 'do_' + command).__doc__)
        else:
            commands = [cmd[3:] for cmd in dir(self) if cmd.startswith('do_')]
            self.send_line_to_b("Valid commands: " +" ".join(commands))

    def do_quit(self):
        """quit: Quit this session"""
        self.send_line_to_b('Goodbye.')
        self.transport.loseConnection()


    def do_start(self, *args):

        what = self.__get_arg(args)

        if what == 'server':

            self.send_line_to_b('Server is already running', True)

        elif what is not None:
            self.send_line_to_b('No command to start %s' % what, True)
        else:
            self.send_line_to_b('Please supply something to start', True)


    def do_stop(self, *args):
        what = self.__get_arg(args)

        if what=='server':
            self.do_quit()

        elif what is not None:
            self.send_line_to_b('No command to stop %s' % what, True)
        else:
            self.send_line_to_b('Please supply something to stop', True)


    def do_show(self, *args):
        what = self.__get_arg(args)

        if what == 'block':
            blockid = self.__get_arg(args, 1)
            if blockid is not None:
                block = Blockchain.Default().GetBlock(blockid)

                if block is not None:
                    [self.send_line_to_b(out) for out in json.dumps(block.ToJson(), indent=2).split("\n")]
                    self.send_line_to_b("Ok... what next?")
                else:
                    print("could not locate block %s " % blockid)
            else:
                print('please specify a block')
            return

        elif what == 'header':

            hid = self.__get_arg(args, 1)
            self.send_line_to_b('Header details:')
            if hid is not None:
                header = Blockchain.Default().GetHeaderBy(hid)

                if header is not None:
                    [self.send_line_to_b(out) for out in json.dumps(header.ToJson(), indent=2).split("\n")]
                    self.send_line_to_b('ok.. what next?')
                else:
                    print("could not locate Header %s " % hid)
            else:
                print('please specify a Header')
            return

        elif what == 'tx':
            txid = self.__get_arg(args, 1)
            self.send_line_to_b('Not implemented yet')
            return
        elif what == 'state':
            height = Blockchain.Default().Height()
            headers = Blockchain.Default().HeaderHeight()
            self.send_line_to_b('Progress: %s / %s ' % (height, headers), True)
            return
        elif what == 'nodes':
            if self.factory and len(self.factory.peers):
                for peer in self.factory.peers:
                    self.send_line_to_b('Peer %s - IO: %s' % (peer.Name(), peer.IOStats()))
            else:
                self.send_line_to_b('Not connected yet')
            return
#        elif what == 'io':
#            if self.factory:
#                br = '%s bytes in, %s bytes out' % ( self.factory.bytes_received(), self.factory.bytes_sent())
#                self.send_line_to_b(br)
#            else:
#                self.send_line_to_b('Not connected yet')
        else:
            self.send_line_to_b("%s is not something i can show" % what)

        self.send_line_to_b("what should i show?  try 'block ID/hash', 'header ID/hash 'tx hash', 'state', 'nodes' ")

    def __get_arg(self, arguments, index=0):
        try:
            return arguments[index].lower()
        except Exception as e:
            self.__log.debug("couldnt get argument at index %s from %s: %s " % (index, arguments,e))
        return None

    def __checkSuccess(self, pageData):
        self.send_line_to_b("Success: got %i bytes." % len(pageData))

    def __checkFailure(self, failure):
        self.send_line_to_b("Failure: " + failure.getErrorMessage())

    def onProtocolConnected(self, protocol):
        if not self.factory:
            self.factory = protocol.factory


    def onProtocolError(self, reason):
        print("Protocol exception %s " % pprint.pprint(reason.protocol))

    def connectionLost(self, reason):
        # stop the reactor, only because this is meant to be run in Stdio.
        if reactor.running:
            reactor.stop()

if __name__ == "__main__":
    stdio.StandardIO(NeoCommandProtocol())
    # start leveldb persist loop
    reactor.run()
