from prompt_toolkit import prompt
from neo.Prompt.InputParser import InputParser
from neo.SmartContract.ContractParameter import ContractParameter
from neo.SmartContract.ContractParameterType import ContractParameterType
from boa.compiler import Compiler
import pprint
import pdb
import dis
import json
from neo.Settings import settings
from neo.logging import log_manager

logger = log_manager.getLogger()


class DebugContext:
    start = None
    end = None
    line = None
    file_id = None
    file_url = None
    files = None

    file_lines = None

    method = None
    method_name = None

    def __init__(self, ctx, files):
        self.start = ctx['start']
        self.end = ctx['end']
        self.line = ctx['file_line_no']
        self.file_id = ctx['file']
        self.method_name = ctx['method']
        for file in files:
            if file['id'] == self.file_id:
                self.file_url = file['url']

        self.file_lines = []

        try:
            default_module = Compiler.load(self.file_url, use_nep8=settings.COMPILER_NEP_8).default
            self.method = default_module.method_by_name(self.method_name)
        except Exception as e:
            logger.error('Could not load module %s %s ' % (self.file_url, e))

        try:
            with open(self.file_url, 'r') as dbg_file:
                for ln in dbg_file:
                    self.file_lines.append(ln.replace('\n', ''))
        except Exception as e:
            logger.error("Could not open file %s : %s " % (self.file_url, e))

    def print_context(self):

        myrange = range(self.line - 3, self.line + 3)
        for index, ln in enumerate(self.file_lines):
            idx = index + 1
            if idx in myrange:

                if idx == self.line:
                    print('[%s]  %s             <<<<<<<<<<<<' % (idx, ln))
                else:
                    print('[%s]  %s' % (idx, ln))

    def print_file(self):
        for index, ln in enumerate(self.file_lines):
            idx = index + 1
            if idx == self.line:
                print('[%s]  %s             <<<<<<<<<<<<' % (idx, ln))
            else:
                print('[%s]  %s' % (idx, ln))

    def print(self):
        print("%s -> %s " % (self.file_url, self.method_name))
        self.print_context()

    def print_method_ops(self):
        dis.dis(self.method.code_object)


class VMDebugger:
    engine = None
    parser = None

    debug_map = None
    debug_context = None
    index = None

    continue_debug = False

    def __init__(self, engine):
        self.engine = engine
        self.parser = InputParser()
        self.debug_map = engine._debug_map
        self.index = engine.CurrentContext.InstructionPointer

    def end(self):
        self.continue_debug = False

    def start(self):

        self.continue_debug = True
        #        pprint.pprint(self.debug_map)

        dbg_title = self.debug_map['avm']['name']
        print("\n")
        print("======= debug engine enter =======")

        ctx = self.get_context()
        ctx.print()

        while self.continue_debug:
            try:
                result = prompt("[%s debug]> " % dbg_title)
            except EOFError:
                # Control-D pressed: quit
                self.continue_debug = False
            except KeyboardInterrupt:
                # Control-C pressed: do nothing
                self.continue_debug = False

            command, arguments = self.parser.parse_input(result)

            if command is not None and len(command) > 0:
                command = command.lower()

                if command in ['quit', 'exit', 'cont']:
                    self.continue_debug = False

                elif command == 'estack':
                    if self.engine._InvocationStack.Count > 0:  # eval stack now only available via ExecutionContext objects in the istack
                        if len(self.engine.CurrentContext.EvaluationStack.Items):
                            for item in self.engine.CurrentContext.EvaluationStack.Items:
                                print(ContractParameter.ToParameter(item).ToJson())
                        else:
                            print("Evaluation stack empty")
                    else:
                        print("Evaluation stack empty")

                elif command == 'istack':
                    print("Invocation Stack:")
                    for item in self.engine.InvocationStack.Items:
                        pprint.pprint(item)
                        print(vars(item))

                elif command == 'astack':
                    if len(self.engine.AltStack.Items):
                        for item in self.engine.AltStack.Items:
                            print(ContractParameter.ToParameter(item).ToJson())
                    else:
                        print("Alt Stack Empty")

                elif command == 'rstack':
                    items = self.engine.ResultStack.Items
                    if len(items):
                        for item in items:
                            pprint.pprint(item)
                    else:
                        print("Result stack empty")

                elif command == 'ctx':
                    ctx.print()

                elif command == 'file':
                    ctx.print_file()

                elif command == 'ops':
                    ctx.print_method_ops()

                elif command == 'pdb':
                    pdb.set_trace()

                elif command == 'help':
                    print("Use one of [estack, istack, astack, exit, quit, ctx, file, ops, pdb, or any local variable]")

                elif command in ctx.method.scope:
                    try:
                        idx = ctx.method.scope[command]
                        value = self.engine.AltStack.Items[-1].GetArray()[idx]
                        param = ContractParameter.ToParameter(value)
                        print("\n")
                        print('%s = %s [%s]' % (command, json.dumps(param.Value.ToJson(), indent=4) if param.Type == ContractParameterType.InteropInterface else param.Value, param.Type))
                        print("\n")
                    except Exception as e:
                        logger.error("Could not lookup item %s: %s " % (command, e))
                else:
                    print("unknown command: %s " % command)

        print("======= debug engine exit =======")
        print("\n")

    def get_context(self):
        files = self.debug_map['files']
        for item in self.debug_map['map']:
            if item['start'] == self.index:
                ctx = DebugContext(item, files)
                return ctx
