import os
import psutil
import datetime
from neo.Prompt.CommandBase import CommandBase, CommandDesc, ParameterDesc
from neo.Prompt.PromptData import PromptData
from neo.Prompt.Utils import get_arg
from neo.Core.Blockchain import Blockchain
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
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
        self.register_sub_command(CommandShowState())
        self.register_sub_command(CommandShowNotifications())
        self.register_sub_command(CommandShowAccount())
        self.register_sub_command(CommandShowAsset())
        self.register_sub_command(CommandShowContract())

    def command_desc(self):
        return CommandDesc('show', 'show data from the blockchain')

    def execute(self, arguments):
        item = get_arg(arguments)

        if not item:
            print("run `show help` to see supported queries")
            return

        try:
            return self.execute_sub_command(item, arguments[1:])
        except KeyError:
            print(f"show: {item} is an invalid parameter")
            return


class CommandShowBlock(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        item = get_arg(arguments)
        txarg = get_arg(arguments, 1)

        block = Blockchain.Default().GetBlock(item)

        if block is not None:
            block.LoadTransactions()
            bjson = json.dumps(block.ToJson(), indent=4)
            if txarg and 'tx' in txarg:
                txs = []
                for tx in block.FullTransactions:
                    tjson = json.dumps(tx.ToJson(), indent=4)
                    tokens = [("class:number", tjson)]
                    print_formatted_text(FormattedText(tokens), style=PromptData.Prompt.token_style)
                    txs.append(tx.ToJson())
                return txs

            tokens = [("class:number", bjson)] 
            print_formatted_text(FormattedText(tokens), style=PromptData.Prompt.token_style)
            return block.ToJson()

        else:
            print("Could not locate block %s" % item)
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

        header = Blockchain.Default().GetHeaderBy(item)
        if header is not None:
            hjson = (json.dumps(header.ToJson(), indent=4))
            tokens = [("class:number", hjson)]
            print_formatted_text(FormattedText(tokens), style=PromptData.Prompt.token_style)
            return header.ToJson()
        else:
            print("Could not locate header %s\n" % item)
            return

    def command_desc(self):
        p1 = ParameterDesc('index/hash', 'the index or scripthash of the block header')
        return CommandDesc('header', 'show the header of a specified block', [p1])


class CommandShowTx(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        try:
            txid = UInt256.ParseString(get_arg(arguments))
            tx, height = Blockchain.Default().GetTransaction(txid)
            if height > -1:
                jsn = tx.ToJson()
                jsn['height'] = height
                jsn['unspents'] = [uns.ToJson(tx.outputs.index(uns)) for uns in
                                   Blockchain.Default().GetAllUnspent(txid)]
                tokens = [("class:command", json.dumps(jsn, indent=4))]
                print_formatted_text(FormattedText(tokens), style=PromptData.Prompt.token_style)
                return jsn
            else:
                print(f"Could not find transaction for hash {txid}")
                return
        except Exception as e:
            print("Could not find transaction from args: %s (%s)" % (e, arguments))
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
        print_formatted_text(FormattedText([("class:number", out)]), style=PromptData.Prompt.token_style)
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
            print_formatted_text(FormattedText([("class:number", out)]), style=PromptData.Prompt.token_style)
            return out
        else:
            print("Not connected yet\n")
            return

    def command_desc(self):
        return CommandDesc('nodes', 'show connected peers')


class CommandShowState(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments=None):
        height = Blockchain.Default().Height
        headers = Blockchain.Default().HeaderHeight

        diff = height - PromptData.Prompt.start_height
        now = datetime.datetime.utcnow()
        difftime = now - PromptData.Prompt.start_dt

        mins = difftime / datetime.timedelta(minutes=1)
        secs = mins * 60

        bpm = 0
        tps = 0
        if diff > 0 and mins > 0:
            bpm = diff / mins
            tps = Blockchain.Default().TXProcessed / secs

        out = "Progress: %s / %s\n" % (height, headers)
        out += "Block-cache length %s\n" % Blockchain.Default().BlockCacheCount
        out += "Blocks since program start %s\n" % diff
        out += "Time elapsed %s mins\n" % mins
        out += "Blocks per min %s \n" % bpm
        out += "TPS: %s \n" % tps
        tokens = [("class:number", out)]
        print_formatted_text(FormattedText(tokens), style=PromptData.Prompt.token_style)
        return out

    def command_desc(self):
        return CommandDesc('state', 'show the status of the node')


class CommandShowNotifications(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        if NotificationDB.instance() is None:
            print("No notification DB Configured")
            return

        item = get_arg(arguments, 0)
        events = []
        if len(item) == 34 and item[0] == 'A':
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
            return events
        else:
            print("No events found for %s" % item)
            return

    def command_desc(self):
        p1 = ParameterDesc('block_index/address', 'the block or address to show notifications for')
        return CommandDesc('notifications', 'show specified contract execution notifications', [p1])


class CommandShowAccount(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        item = get_arg(arguments)

        account = Blockchain.Default().GetAccountState(item, print_all_accounts=True)

        if account is not None:
            bjson = json.dumps(account.ToJson(), indent=4)
            tokens = [("class:number", bjson)]
            print_formatted_text(FormattedText(tokens), style=PromptData.Prompt.token_style)
            return account.ToJson()
        else:
            print("Account %s not found" % item)
            return

    def command_desc(self):
        p1 = ParameterDesc('address', 'the address to show')
        return CommandDesc('account', 'show the assets (NEO/GAS) held by a specified address', [p1])


class CommandShowAsset(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        item = get_arg(arguments)

        if item.lower() == "all":
            assets = Blockchain.Default().ShowAllAssets()
            print("Assets: %s" % assets)
            return assets

        if item.lower() == 'neo':
            assetId = Blockchain.Default().SystemShare().Hash
        elif item.lower() == 'gas':
            assetId = Blockchain.Default().SystemCoin().Hash
        else:
            try:
                assetId = UInt256.ParseString(item)
            except Exception as e:
                print("Could not find assetId from args: %s (%s)" % (e, arguments))
                return

        asset = Blockchain.Default().GetAssetState(assetId.ToBytes())

        if asset is not None:
            bjson = json.dumps(asset.ToJson(), indent=4)
            tokens = [("class:number", bjson)]
            print_formatted_text(FormattedText(tokens), style=PromptData.Prompt.token_style)
            return asset.ToJson()
        else:
            print("Asset %s not found" % item)
            return

    def command_desc(self):
        p1 = ParameterDesc('name/assetId/all', 'the name or assetId of the asset, or "all" shows all assets\n\n')
        f"{' ':>17} Example:\n"
        f"{' ':>20} 'neo' or 'c56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b'\n"
        f"{' ':>20} 'gas' or '602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7'\n"
        return CommandDesc('asset', 'show a specified asset', [p1])


class CommandShowContract(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        item = get_arg(arguments)

        if item.lower() == "all":
            contracts = Blockchain.Default().ShowAllContracts()
            print("Contracts: %s" % contracts)
            return contracts

        contract = Blockchain.Default().GetContract(item)

        if contract is not None:
            contract.DetermineIsNEP5()
            bjson = json.dumps(contract.ToJson(), indent=4)
            tokens = [("class:number", bjson)]
            print_formatted_text(FormattedText(tokens), style=PromptData.Prompt.token_style)
            return contract.ToJson()
        else:
            print("Contract %s not found" % item)
            return

    def command_desc(self):
        p1 = ParameterDesc('hash/all', 'the scripthash of the contract, or "all" shows all contracts')
        return CommandDesc('contract', 'show a specified smart contract', [p1])
