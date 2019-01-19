import os
import psutil
import datetime
from neo.Prompt.CommandBase import CommandBase, CommandDesc, ParameterDesc
from neo.Prompt.PromptData import PromptData
from neo.Prompt.Utils import get_arg
from neo.Core.Blockchain import Blockchain
from neocore.UInt256 import UInt256
from neocore.UInt160 import UInt160
from neo.IO.MemoryStream import StreamManager
from neo.Network.NodeLeader import NodeLeader
from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB
from neo.logging import log_manager
from neo.Prompt.PromptPrinter import prompt_print as print
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
        return CommandDesc('show', 'show various node and blockchain data')

    def execute(self, arguments):
        item = get_arg(arguments)

        if not item:
            print(f"run `{self.command_desc().command} help` to see supported queries")
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
            print("Please specify the required parameter")
            return

    def command_desc(self):
        p1 = ParameterDesc('attribute', 'block index or script hash')
        p2 = ParameterDesc('tx', 'flag to only show block transactions', optional=True)
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
            print("Please specify the required parameter")
            return

    def command_desc(self):
        p1 = ParameterDesc('attribute', 'header index or script hash')
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
            print("Please specify the required parameter")
            return

    def command_desc(self):
        p1 = ParameterDesc('hash', 'transaction script hash')
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
            for i, peer in enumerate(NodeLeader.Instance().Peers):
                out += f"Peer {i} {peer.Name():>12} - {peer.address:>21} - IO {peer.IOStats()}\n"
            print(out)
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
        print(out)
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

        item = get_arg(arguments)
        if item is not None:
            if item[0:2] == "0x":
                item = item[2:]

            if len(item) == 34 and item[0] == 'A':
                events = NotificationDB.instance().get_by_addr(item)

            elif len(item) == 40:
                events = NotificationDB.instance().get_by_contract(item)

            else:
                try:
                    block_height = int(item)
                    if block_height < Blockchain.Default().Height:
                        events = NotificationDB.instance().get_by_block(block_height)
                    else:
                        print("Block %s not found" % block_height)
                        return
                except Exception:
                    print("Could not find notifications from args: %s" % arguments)
                    return

            if len(events):
                [print(json.dumps(e.ToJson(), indent=4)) for e in events]
                return events
            else:
                print("No events found for %s" % item)
                return
        else:
            print("Please specify the required parameter")
            return

    def command_desc(self):
        p1 = ParameterDesc('attribute', 'block index, an address, or contract script hash to show notifications for')
        return CommandDesc('notifications', 'show specified contract execution notifications', [p1])


class CommandShowAccount(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        item = get_arg(arguments)
        if item is not None:
            account = Blockchain.Default().GetAccountState(item, print_all_accounts=True)

            if account is not None:
                print(json.dumps(account.ToJson(), indent=4))
                return account.ToJson()
            else:
                print("Account %s not found" % item)
                return
        else:
            print("Please specify the required parameter")
            return

    def command_desc(self):
        p1 = ParameterDesc('address', 'public NEO address')
        return CommandDesc('account', 'show the assets (NEO/GAS) held by a specified address', [p1])


class CommandShowAsset(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        item = get_arg(arguments)
        if item is not None:
            if item.lower() == "all":
                assets = Blockchain.Default().ShowAllAssets()
                assetlist = []
                for asset in assets:
                    state = Blockchain.Default().GetAssetState(asset.decode('utf-8')).ToJson()
                    asset_dict = {state['name']: state['assetId']}
                    assetlist.append(asset_dict)
                print(json.dumps(assetlist, indent=4))
                return assetlist

            if item.lower() == 'neo':
                assetId = Blockchain.Default().SystemShare().Hash
            elif item.lower() == 'gas':
                assetId = Blockchain.Default().SystemCoin().Hash
            else:
                try:
                    assetId = UInt256.ParseString(item)
                except Exception:
                    print("Could not find asset from args: %s" % arguments)
                    return

            asset = Blockchain.Default().GetAssetState(assetId.ToBytes())

            if asset is not None:
                print(json.dumps(asset.ToJson(), indent=4))
                return asset.ToJson()
            else:
                print("Asset %s not found" % item)
                return
        else:
            print('Please specify the required parameter')
            return

    def command_desc(self):
        p1 = ParameterDesc('attribute',
                           'asset name, assetId, or "all"\n\n'
                           f"{' ':>17} Example:\n"
                           f"{' ':>20} 'neo' or 'c56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b'\n"
                           f"{' ':>20} 'gas' or '602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7'\n")
        return CommandDesc('asset', 'show a specified asset', [p1])


class CommandShowContract(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        item = get_arg(arguments)
        if item is not None:
            if item.lower() == "all":
                contracts = Blockchain.Default().ShowAllContracts()
                contractlist = []
                for contract in contracts:
                    state = Blockchain.Default().GetContract(contract.decode('utf-8')).ToJson()
                    contract_dict = {state['name']: state['hash']}
                    contractlist.append(contract_dict)
                print(json.dumps(contractlist, indent=4))
                return contractlist

            try:
                hash = UInt160.ParseString(item).ToBytes()
            except Exception:
                print("Could not find contract from args: %s" % arguments)
                return

            contract = Blockchain.Default().GetContract(hash)

            if contract is not None:
                contract.DetermineIsNEP5()
                print(json.dumps(contract.ToJson(), indent=4))
                return contract.ToJson()
            else:
                print("Contract %s not found" % item)
                return
        else:
            print('Please specify the required parameter')
            return

    def command_desc(self):
        p1 = ParameterDesc('attribute', 'contract script hash, or "all"')
        return CommandDesc('contract', 'show a specified smart contract', [p1])
