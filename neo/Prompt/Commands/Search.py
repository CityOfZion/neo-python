from neo.Prompt.CommandBase import CommandBase, CommandDesc, ParameterDesc
from neo.Prompt.PromptData import PromptData
from neo.Prompt.Utils import get_arg
from neo.Core.Blockchain import Blockchain
from neo.logging import log_manager
from neo.Prompt.PromptPrinter import prompt_print as print
import json

logger = log_manager.getLogger()


class CommandSearch(CommandBase):
    def __init__(self):
        super().__init__()

        self.register_sub_command(CommandSearchAsset())
        self.register_sub_command(CommandSearchContract())

    def command_desc(self):
        return CommandDesc('search', 'search the blockchain')

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


class CommandSearchAsset(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        item = get_arg(arguments)
        if item is not None:
            results = Blockchain.Default().SearchAssetState(item)
            print("Found %s results for %s" % (len(results), item))
            for asset in results:
                print(json.dumps(asset.ToJson(), indent=4))
            return results
        else:
            print("run `%s %s help` to see supported queries" % (CommandSearch().command_desc().command, self.command_desc().command))
            return

    def command_desc(self):
        p1 = ParameterDesc('query', 'name, issuer, or admin')
        return CommandDesc('asset', 'perform an asset search', [p1])


class CommandSearchContract(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        item = get_arg(arguments)
        if item is not None:
            contracts = Blockchain.Default().SearchContracts(query=item)
            print("Found %s results for %s" % (len(contracts), item))
            for contract in contracts:
                print(json.dumps(contract.ToJson(), indent=4))
            return contracts
        else:
            print("run `%s %s help` to see supported queries" % (CommandSearch().command_desc().command, self.command_desc().command))
            return

    def command_desc(self):
        p1 = ParameterDesc('query', 'name, author, description, or email')
        return CommandDesc('contract', 'perform a contract search', [p1])
