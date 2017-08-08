#!/usr/bin/env python

# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Example using stdio, Deferreds, LineReceiver and twisted.web.client.

Note that the WebCheckerCommandProtocol protocol could easily be used in e.g.
a telnet server instead; see the comments for details.

Based on an example by Abe Fettig.
"""

from neo.Network.NeoNode import NeoNode
from neo.Network.NeoNodeFactory import NeoFactory


from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo import Settings

blockchain = LevelDBBlockchain(Settings.LEVELDB_PATH)
Blockchain.RegisterBlockchain(blockchain)

from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
from twisted.internet import stdio, reactor
from twisted.protocols import basic
from twisted.web import client

class NeoCommandProtocol(basic.LineReceiver):
    delimiter = b'\n' # unix terminal style newlines. remove this line
                     # for use with Telnet

    nodes = []

    def send_line_to_b(self, value):
        return self.sendLine(value.encode('utf-8'))

    def connectionMade(self):
        self.send_line_to_b("Web checker console. Type 'help' for help.")

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
            try:
                method(*args)
            except Exception as e:
                self.send_line_to_b('Error: ' + str(e))

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

    def do_check(self, url):
        """check <url>: Attempt to download the given web page"""
        client.Agent(reactor).request('GET', url).addCallback(
            client.readBody).addCallback(
            self.__checkSuccess).addErrback(
            self.__checkFailure)

    def do_startserver(self):
        print("do start server")
        for bootstrap in Settings.SEED_LIST:
            host, port = bootstrap.split(":")
            point = TCP4ClientEndpoint(reactor, host, int(port))
            node = connectProtocol(point, NeoNode(NeoFactory))

    def do_stopserver(self):
        print("do stop server")
        for n in self.nodes:
            n.disconnect()

    def do_showstate(self):
        height = Blockchain.Default().Height()
        headers = Blockchain.Default().HeaderHeight()
        self.send_line_to_b('Progress: %s / %s ' % (height, headers))


    def __checkSuccess(self, pageData):
        self.send_line_to_b("Success: got %i bytes." % len(pageData))

    def __checkFailure(self, failure):
        self.send_line_to_b("Failure: " + failure.getErrorMessage())

    def connectionLost(self, reason):
        # stop the reactor, only because this is meant to be run in Stdio.
        reactor.stop()

if __name__ == "__main__":
    stdio.StandardIO(NeoCommandProtocol())
    reactor.run()
