import os
import psutil
import datetime
from neo.Prompt.CommandBase import CommandBase, CommandDesc, ParameterDesc
from neo.Prompt.PromptData import PromptData
from neo.Prompt.Utils import get_arg
from neo.Core.Blockchain import Blockchain
from neocore.UInt256 import UInt256
from neo.IO.MemoryStream import StreamManager
from neo.Network.NodeLeader import NodeLeader
from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB
from neo.logging import log_manager
import json


logger = log_manager.getLogger()


class CommandShow(CommandBase):
    def __init__(self):
        super().__init__()

        self.register_sub_command(CommandShowBlock())
        self.register_sub_command(CommandShowHeader())
        self.register_sub_command(CommandShowTx())
        self.register_sub_command(CommandShowMem())
        self.register_sub_command(CommandShowNodes(), ['node'])

    def command_desc(self):
        return CommandDesc('show', 'show useful data')

    def execute(self, arguments):
        item = get_arg(arguments)

        if not item:
            print("run `%s help` to see supported queries" % self.command_desc().command)
            return

        try:
            return self.execute_sub_command(item, arguments[1:])
        except KeyError:
            print(f"{item} is an invalid parameter")
            return


class CommandShowBlock(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        item = get_arg(arguments)
        txarg = get_arg(arguments, 1)
        if item is not None:
            block = Blockchain.Default().GetBlock(item)

            if block is not None:
                block.LoadTransactions()

                if txarg and 'tx' in txarg:
                    txs = []
                    for tx in block.FullTransactions:
                        print(json.dumps(tx.ToJson(), indent=4))
                        txs.append(tx.ToJson())
                    return txs

                print(json.dumps(block.ToJson(), indent=4))
                return block.ToJson()

            else:
                print("Could not locate block %s" % item)
                return
        else:
            print("please specify a block")
            return

    def command_desc(self):
        p1 = ParameterDesc('index/hash', 'the index or scripthash of the block')
        p2 = ParameterDesc('tx', 'arg to only show block transactions', optional=True)
        return CommandDesc('block', 'show a specified block', [p1, p2])


class CommandShowHeader(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        item = get_arg(arguments)
        if item is not None:
            header = Blockchain.Default().GetHeaderBy(item)
            if header is not None:
                print(json.dumps(header.ToJson(), indent=4))
                return header.ToJson()
            else:
                print("Could not locate header %s\n" % item)
                return
        else:
            print("Please specify a header")
            return

    def command_desc(self):
        p1 = ParameterDesc('index/hash', 'the index or scripthash of the block header')
        return CommandDesc('header', 'show the header of a specified block', [p1])


class CommandShowTx(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        if len(arguments):
            try:
                txid = UInt256.ParseString(get_arg(arguments))
                tx, height = Blockchain.Default().GetTransaction(txid)
                if height > -1:
                    jsn = tx.ToJson()
                    jsn['height'] = height
                    jsn['unspents'] = [uns.ToJson(tx.outputs.index(uns)) for uns in
                                    Blockchain.Default().GetAllUnspent(txid)]
                    print(json.dumps(jsn, indent=4))
                    return jsn
                else:
                    print(f"Could not find transaction for hash {txid}")
                    return
            except Exception:
                print("Could not find transaction from args: %s" % arguments)
                return
        else:
            print("Please specify a TX hash")
            return

    def command_desc(self):
        p1 = ParameterDesc('hash', 'the scripthash of the transaction')
        return CommandDesc('tx', 'show a specified transaction', [p1])


class CommandShowMem(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments=None):
        process = psutil.Process(os.getpid())
        total = process.memory_info().rss
        totalmb = total / (1024 * 1024)
        out = "Total: %s MB\n" % totalmb
        out += "Total buffers: %s\n" % StreamManager.TotalBuffers()
        print(out)
        return out

    def command_desc(self):
        return CommandDesc('mem', 'show memory in use and number of buffers')


class CommandShowNodes(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments=None):
        if len(NodeLeader.Instance().Peers) > 0:
            out = "Total Connected: %s\n" % len(NodeLeader.Instance().Peers)
            for peer in NodeLeader.Instance().Peers:
                out += "Peer %s - IO: %s\n" % (peer.Name(), peer.IOStats())
            print(out)
            return out
        else:
            print("Not connected yet\n")
            return

    def command_desc(self):
        return CommandDesc('nodes', 'show connected peers')
