from neo.Prompt.CommandBase import CommandBase, CommandDesc, ParameterDesc
from neo.Prompt.PromptData import PromptData
from neo.Prompt.Utils import get_arg
from neo.Prompt.Commands.BuildNRun import Build, BuildAndRun, LoadAndRun
from neo.Core.Blockchain import Blockchain

from neo.logging import log_manager
import json


logger = log_manager.getLogger()


class CommandSC(CommandBase):
    def __init__(self):
        super().__init__()

        self.register_sub_command(CommandSCBuild())
        self.register_sub_command(CommandSCBuildRun())
        self.register_sub_command(CommandSCLoadRun())

    def command_desc(self):
        return CommandDesc('sc', 'develop smart contracts')

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
        tx, result, total_ops, engine = BuildAndRun(arguments, PromptData.Wallet)
        Blockchain.Default().Resume()
        return tx, result, total_ops, engine

    def command_desc(self):
        p1 = ParameterDesc('path', 'the path to the desired Python (.py) file')
        p2 = ParameterDesc('params', 'the input parameter types')
        p3 = ParameterDesc('returntype', 'the returntype of the smart contract output')
        p4 = ParameterDesc('storage', 'boolean input to determine if smart contract requires storage')
        p5 = ParameterDesc('dynamic_invoke', 'boolean input to determine if smart contract requires dynamic invoke')
        p6 = ParameterDesc('payable', 'boolean input to determine if smart contract is payable')
        p7 = ParameterDesc('inputs', 'the test parameters to input, or use "--i" for prompted parameter input')
        p8 = ParameterDesc('--no-parse-addr', 'a flag to turn off address parsing when input into the smart contract', optional=True)
        p9 = ParameterDesc('--from-addr={addr}', 'address to send invocation fee from', optional=True)
        p10 = ParameterDesc('--owners=[{addr}, ...]', 'specify invocation owners', optional=True)
        p11 = ParameterDesc('--tx-attr=[{"usage": <value>,"data":"<remark>"}, ...]', 'specify unique invocation attributes\n\n'
                            f"{' ':>17} Examples:\n"
                            f"{' ':>20} build_run path.py 0710 05 True False False input1 input2\n"
                            f"{' ':>20} build_run path.py 0710 05 True False False --i\n\n"
                            f"{' ':>17} For more information about parameter types see\n"
                            f"{' ':>17} https://neo-python.readthedocs.io/en/latest/data-types.html#contractparametertypes", optional=True)
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
        tx, result, total_ops, engine = LoadAndRun(arguments, PromptData.Wallet)
        Blockchain.Default().Resume()
        return tx, result, total_ops, engine

    def command_desc(self):
        p1 = ParameterDesc('path', 'the path to the desired Python (.py) file')
        p2 = ParameterDesc('params', 'the input parameter types')
        p3 = ParameterDesc('returntype', 'the returntype of the smart contract output')
        p4 = ParameterDesc('storage', 'boolean input to determine if smart contract requires storage')
        p5 = ParameterDesc('dynamic_invoke', 'boolean input to determine if smart contract requires dynamic invoke')
        p6 = ParameterDesc('payable', 'boolean input to determine if smart contract is payable')
        p7 = ParameterDesc('inputs', 'the test parameters to input, or use "--i" for prompted parameter input')
        p8 = ParameterDesc('--no-parse-addr', 'a flag to turn off address parsing when input into the smart contract', optional=True)
        p9 = ParameterDesc('--from-addr={addr}', 'address to send invocation fee from\n\n'
                           f"{' ':>17} Examples:\n"
                           f"{' ':>20} load_run path.py 0710 05 True False False input1 input2\n"
                           f"{' ':>20} load_run path.py 0710 05 True False False --i\n\n"
                           f"{' ':>17} For more information about parameter types see\n"
                           f"{' ':>17} https://neo-python.readthedocs.io/en/latest/data-types.html#contractparametertypes", optional=True)
        params = [p1, p2, p3, p4, p5, p6, p7, p8, p9]
        return CommandDesc('load_run', 'load a specified smart contract (.avm) file and test it', params=params)
