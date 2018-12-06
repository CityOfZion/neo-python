from neo.Prompt.CommandBase import CommandBase, CommandDesc, ParameterDesc
from neo.Prompt.PromptData import PromptData
from neo.Prompt.Utils import get_arg
from neo.Core.Blockchain import Blockchain
from neo.logging import log_manager
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
            print("run `%s help` to see supported queries" % self.command_desc().command)
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

        results = Blockchain.Default().SearchAssetState(item)
        print("Found %s results for %s" % (len(results), item))
        for asset in results:
            print(json.dumps(asset.ToJson(), indent=4))
        return results

    def command_desc(self):
        p1 = ParameterDesc('query', 'supports name, issuer, or admin searches')
        return CommandDesc('asset', 'perform an asset search', [p1])


class CommandSearchContract(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        item = get_arg(arguments)

        contracts = Blockchain.Default().SearchContracts(query=item)
        print("Found %s results for %s" % (len(contracts), item))
        for contract in contracts:
            print(json.dumps(contract.ToJson(), indent=4))
        return contracts

    def command_desc(self):
        p1 = ParameterDesc('query', 'supports name, author, description, or email searches')
        return CommandDesc('contract', 'perform a contract search', [p1])
