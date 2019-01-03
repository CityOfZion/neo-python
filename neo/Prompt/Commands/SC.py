from neo.Prompt.CommandBase import CommandBase, CommandDesc, ParameterDesc
from neo.Prompt.PromptData import PromptData
from neo.Prompt import Utils as PromptUtils
from neo.Prompt.Commands.BuildNRun import Build, BuildAndRun, LoadAndRun
from neo.Prompt.Commands.Invoke import TestInvokeContract, InvokeContract
from neo.Core.Blockchain import Blockchain
from neocore.UInt160 import UInt160
from neocore.Fixed8 import Fixed8
from prompt_toolkit import prompt
from neo.SmartContract.ContractParameter import ContractParameter

from neo.logging import log_manager

logger = log_manager.getLogger()


class CommandSC(CommandBase):
    def __init__(self):
        super().__init__()

        self.register_sub_command(CommandSCBuild())
        self.register_sub_command(CommandSCBuildRun())
        self.register_sub_command(CommandSCLoadRun())
        self.register_sub_command(CommandSCTestInvoke())

    def command_desc(self):
        return CommandDesc('sc', 'develop smart contracts')

    def execute(self, arguments):
        item = PromptUtils.get_arg(arguments)

        if not item:
            print(f"run `{self.command_desc().command} help` to see supported queries")
            return

        try:
            return self.execute_sub_command(item, arguments[1:])
        except KeyError:
            print(f"{item} is an invalid parameter")
            return


class CommandSCBuild(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        if len(arguments) != 1:
            print("Please specify the required parameter")
            return

        Blockchain.Default().Pause()
        contract_script = Build(arguments)
        Blockchain.Default().Resume()
        return contract_script

    def command_desc(self):
        p1 = ParameterDesc('path', 'the path to the desired Python (.py) file')
        return CommandDesc('build', 'compile a specified Python (.py) script into a smart contract (.avm) file', [p1])


class CommandSCBuildRun(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        if len(arguments) < 7:
            print("Please specify the required parameters")
            return

        Blockchain.Default().Pause()
        try:
            tx, result, total_ops, engine = BuildAndRun(arguments, PromptData.Wallet)
        except TypeError:
            print(f'run `{CommandSC().command_desc().command} {self.command_desc().command} help` to see supported queries')
            Blockchain.Default().Resume()
            return
        Blockchain.Default().Resume()
        return tx, result, total_ops, engine

    def command_desc(self):
        p1 = ParameterDesc('path', 'the path to the desired Python (.py) file')
        p2 = ParameterDesc('storage', 'boolean input to determine if smart contract requires storage')
        p3 = ParameterDesc('dynamic_invoke', 'boolean input to determine if smart contract requires dynamic invoke')
        p4 = ParameterDesc('payable', 'boolean input to determine if smart contract is payable')
        p5 = ParameterDesc('params', 'the input parameter types of the smart contract')
        p6 = ParameterDesc('returntype', 'the returntype of the smart contract output')
        p7 = ParameterDesc('inputs', 'the test parameters fed to the smart contract, or use "--i" for prompted parameter input')
        p8 = ParameterDesc('--no-parse-addr', 'a flag to turn off address parsing when input into the smart contract', optional=True)
        p9 = ParameterDesc('--from-addr', 'source address to take fee funds from (if not specified, take first address in wallet)', optional=True)
        p10 = ParameterDesc('--owners', 'a list of NEO addresses indicating the transaction owners e.g. --owners=[address1,address2]', optional=True)
        p11 = ParameterDesc('--tx-attr',
                            'a list of transaction attributes to attach to the transaction\n\n'
                            f"{' ':>17} See: http://docs.neo.org/en-us/network/network-protocol.html section 4 for a description of possible attributes\n\n"
                            f"{' ':>17} Example\n"
                            f"{' ':>20} --tx-attr=[{{\"usage\": <value>,\"data\":\"<remark>\"}}, ...]\n"
                            f"{' ':>20} --tx-attr=[{{\"usage\": 0x90,\"data\":\"my brief description\"}}]\n\n"
                            f"{' ':>17} Usage Examples:\n"
                            f"{' ':>20} build_run path.py True False False 0710 05 input1 input2\n"
                            f"{' ':>20} build_run path.py True False False 0710 05 --i\n\n"
                            f"{' ':>17} For more information about parameter types see\n"
                            f"{' ':>17} https://neo-python.readthedocs.io/en/latest/data-types.html#contractparametertypes\n", optional=True)
        params = [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11]
        return CommandDesc('build_run', 'compile a specified Python (.py) script into a smart contract (.avm) file and test it', params=params)


class CommandSCLoadRun(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        if len(arguments) < 7:
            print("Please specify the required parameters")
            return

        Blockchain.Default().Pause()
        try:
            tx, result, total_ops, engine = LoadAndRun(arguments, PromptData.Wallet)
        except TypeError:
            print(f'run `{CommandSC().command_desc().command} {self.command_desc().command} help` to see supported queries')
            Blockchain.Default().Resume()
            return
        Blockchain.Default().Resume()
        return tx, result, total_ops, engine

    def command_desc(self):
        p1 = ParameterDesc('path', 'the path to the desired smart contract (.avm) file')
        p2 = ParameterDesc('storage', 'boolean input to determine if smart contract requires storage')
        p3 = ParameterDesc('dynamic_invoke', 'boolean input to determine if smart contract requires dynamic invoke')
        p4 = ParameterDesc('payable', 'boolean input to determine if smart contract is payable')
        p5 = ParameterDesc('params', 'the input parameter types of the smart contract')
        p6 = ParameterDesc('returntype', 'the returntype of the smart contract output')
        p7 = ParameterDesc('inputs', 'the test parameters fed to the smart contract, or use "--i" for prompted parameter input')
        p8 = ParameterDesc('--no-parse-addr', 'a flag to turn off address parsing when input into the smart contract', optional=True)
        p9 = ParameterDesc('--from-addr',
                           'source address to take fee funds from (if not specified, take first address in wallet)\n\n'
                           f"{' ':>17} Usage Examples:\n"
                           f"{' ':>20} load_run path.py True False False 0710 05 input1 input2\n"
                           f"{' ':>20} load_run path.py True False False 0710 05 --i\n\n"
                           f"{' ':>17} For more information about parameter types see\n"
                           f"{' ':>17} https://neo-python.readthedocs.io/en/latest/data-types.html#contractparametertypes\n", optional=True)
        params = [p1, p2, p3, p4, p5, p6, p7, p8, p9]
        return CommandDesc('load_run', 'load a specified smart contract (.avm) file and test it', params=params)


class CommandSCTestInvoke(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        wallet = PromptData.Wallet
        if not wallet:
            print("Please open a wallet")
            return False

        arguments, from_addr = PromptUtils.get_from_addr(arguments)
        arguments, invoke_attrs = PromptUtils.get_tx_attr_from_args(arguments)
        arguments, owners = PromptUtils.get_owners_from_params(arguments)

        if len(arguments) < 2:
            print("Please specify the required parameters")
            return False

        hash_string = arguments[0]
        try:
            script_hash = UInt160.ParseString(hash_string)
        except Exception:
            # because UInt160 throws a generic exception. Should be fixed in the future
            print("Invalid script hash")
            return False

        tx, fee, results, num_ops = TestInvokeContract(wallet, arguments, from_addr=from_addr, invoke_attrs=invoke_attrs, owners=owners)
        if tx is not None and results is not None:

            parameterized_results = [ContractParameter.ToParameter(item) for item in results]

            print(
                "\n-------------------------------------------------------------------------------------------------------------------------------------")
            print("Test invoke successful")
            print(f"Total operations: {num_ops}")
            print(f"Results {str([item.ToJson() for item in parameterized_results])}")
            print(f"Invoke TX GAS cost: {tx.Gas.value / Fixed8.D}")
            print(f"Invoke TX fee: {fee.value / Fixed8.D}")
            print(
                "-------------------------------------------------------------------------------------------------------------------------------------\n")
            print("Enter your password to continue and invoke on the network\n")

            tx.Attributes = invoke_attrs

            passwd = prompt("[password]> ", is_password=True)
            if not wallet.ValidatePassword(passwd):
                return print("Incorrect password")

            return InvokeContract(wallet, tx, fee, from_addr=from_addr, owners=owners)
        else:
            print("Error testing contract invoke")
            return False

    def command_desc(self):
        p1 = ParameterDesc('contract', 'token contract hash (script_hash)')
        p2 = ParameterDesc('inputs', 'the test parameters fed to the smart contract, or use "--i" for prompted parameter input')
        p3 = ParameterDesc('--attach-neo', 'amount of neo to attach to the transaction. Required if --attach-gas is not specified', optional=True)
        p4 = ParameterDesc('--attach-gas', 'amount of gas to attach to the transaction. Required if --attach-neo is not specified', optional=True)
        p5 = ParameterDesc('--no-parse-addr', 'a flag to turn off address parsing when input into the smart contract', optional=True)
        p6 = ParameterDesc('--from-addr', 'source address to take fee funds from (if not specified, take first address in wallet)', optional=True)
        p7 = ParameterDesc('--owners', 'a list of NEO addresses indicating the transaction owners e.g. --owners=[address1,address2]', optional=True)
        p8 = ParameterDesc('--tx-attr',
                           'a list of transaction attributes to attach to the transaction\n\n'
                           f"{' ':>17} See: http://docs.neo.org/en-us/network/network-protocol.html section 4 for a description of possible attributes\n\n"
                           f"{' ':>17} Example\n"
                           f"{' ':>20} --tx-attr=[{{\"usage\": <value>,\"data\":\"<remark>\"}}, ...]\n"
                           f"{' ':>20} --tx-attr=[{{\"usage\": 0x90,\"data\":\"my brief description\"}}]\n\n", optional=True)
        params = [p1, p2, p3, p4, p5, p6, p7, p8]
        return CommandDesc('invoke', 'Call functions on the smart contract. Will prompt before sending to the network', params=params)
