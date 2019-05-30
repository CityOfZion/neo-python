import json
import io
import binascii
import glob
import traceback
from neo.VM.ExecutionEngine import ExecutionEngine
from neo.VM.ExecutionEngine import ExecutionContext
from neo.VM.RandomAccessStack import RandomAccessStack
from neo.Core.Cryptography.Crypto import Crypto
from neo.Core.UInt160 import UInt160
from typing import Optional
from neo.VM.VMState import VMStateStr
from neo.VM.OpCode import ToName as OpcodeToName
from neo.VM.OpCode import RET
from neo.VM import InteropService
from neo.VM.Debugger import Debugger


class MessageProvider:
    def __init__(self, message: str):
        """
        Args:
            message: expected in format "0xAABB"
        """
        self.message = message[2:].encode()

    def GetMessage(self) -> bytes:
        return self.message


class ScriptTable:
    def __init__(self):
        self.data = dict()  # script_hash:contract

    def GetScript(self, script_hash: bytes) -> Optional[bytes]:
        if script_hash.startswith(b'0x'):
            script_hash = script_hash[2:]
        return self.data.get(script_hash, None)

    def Add(self, script: bytearray) -> None:
        h = bytearray(Crypto.Default().Hash160(script))
        h.reverse()
        self.data[binascii.hexlify(h)] = script


file_count = 0
test_count = 0
skipped_test_count = 0


def main():
    global file_count
    for filename in glob.glob("./**/*.json", recursive=True):
        file_count += 1
        with io.open(filename, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)  # uses dirty UTF-8 BOM header *sigh*
            try:
                execute_test(data)
            except Exception:
                # should never happen, but in case it does
                traceback.print_exc()
                break
    print(f"Executed {test_count} test(s) from {file_count} file(s). Skipped {skipped_test_count} test(s)")


def execute_test(data: dict):
    global test_count, skipped_test_count
    for test in data['tests']:
        test_count += 1
        # interop service
        service = InteropService.InteropService()

        # message provider
        script_container = None

        message = test.get("message", None)
        if message:
            script_container = MessageProvider(message)

        # prepare script table
        scripts = test.get("scriptTable", None)
        script_table = None
        if scripts:
            script_table = ScriptTable()
            for entry in scripts:
                try:
                    script = binascii.unhexlify(entry['script'][2:])
                    script_table.Add(script)
                except binascii.Error:
                    print(f"Skipping test {data['category']}-{data['name']}, cannot read script data")
                    test_count -= 1
                    skipped_test_count += 1
                    continue

        # create engine and run
        engine = ExecutionEngine(crypto=Crypto.Default(), service=service, container=script_container, table=script_table, exit_on_error=True)

        debugger = Debugger(engine)

        # TODO: should enforce 0x<data> rule in the JSON test case
        if test['script'].startswith('0x'):
            script = test['script'][2:]
        else:
            script = test['script']
        try:
            script = binascii.unhexlify(script)
        except binascii.Error:
            print(f"Skipping test {data['category']}-{data['name']}, cannot read script data")
            test_count -= 1
            skipped_test_count += 1
            continue

        engine.LoadScript(script)

        steps = test.get('steps', None)
        if steps is None:
            continue

        for i, step in enumerate(steps):
            actions = step.get('actions', [])
            for action in actions:
                if action == "StepInto":
                    debugger.StepInto()
                elif action == "Execute":
                    debugger.Execute()
                elif action == "StepOver":
                    debugger.StepOver()
                elif action == "StepOut":
                    debugger.StepOut()

            test_name = test.get("name", "")
            msg = f"{data['category']}-{data['name']}-{test_name}-{i}"
            assert_result(engine, step['result'], msg)


def assert_result(engine: ExecutionEngine, result: dict, msg: str):
    state = VMStateStr(engine.State)
    assert state.lower() == result['state'].lower(), f"[{msg}] State differs! Expected: {result['state']} Actual: {state}"

    invocation_stack = result.get("invocationStack", None)
    if invocation_stack:
        assert_invocation_stack(engine.InvocationStack, invocation_stack, msg)

    result_stack = result.get("resultStack", None)
    if result_stack:
        assert_stack_result(engine.ResultStack, result_stack, msg)


def assert_invocation_stack(istack: RandomAccessStack, result: dict, msg: str):
    assert istack.Count == len(result), f"[{msg}] Invocation stack size differs! Expected: {len(result)} Actual: {istack.Count}"

    for expected_context, actual_context in zip(result, reversed(istack.Items)):  # type: ExecutionContext

        expected_script_hash = expected_context['scriptHash'][2:].lower()
        actual_script_hash = binascii.hexlify(actual_context.ScriptHash()).decode()
        assert actual_script_hash == expected_script_hash, f"[{msg}] Script hash differs! Expected: {expected_script_hash} Actual: {actual_script_hash}"

        opcode = RET if actual_context.InstructionPointer >= actual_context.Script.Length else actual_context.Script[actual_context.InstructionPointer]
        expected_next_instruction = expected_context['nextInstruction']
        # hack to work around C#'s lack of having defined enum members for PUSHBYTES2-PUSHBYTES74
        # TODO: remove this once neo-vm is updated to have human readable names for the above enum members
        if expected_next_instruction.isdecimal():
            expected_next_instruction = OpcodeToName(int(expected_next_instruction))

        actual_next_instruction = OpcodeToName(opcode)
        assert actual_next_instruction == expected_next_instruction, f"[{msg}] Next instruction differs! Expected: {expected_next_instruction} Actual: {actual_next_instruction}"

        expected_ip = expected_context['instructionPointer']
        actual_ip = actual_context.InstructionPointer
        assert actual_ip == expected_ip, f"[{msg}] Instruction pointer differs! Expected: {expected_ip} Actual: {actual_ip}"

        eval_stack = expected_context.get("evaluationStack", None)
        if eval_stack:
            assert_stack_result(actual_context.EvaluationStack, eval_stack, msg)

        alt_stack = expected_context.get("altStack", None)
        if alt_stack:
            assert_stack_result(actual_context.AltStack, alt_stack, msg)


def assert_stack_result(stack: RandomAccessStack, result: dict, msg: str):
    assert stack.Count == len(result), f"[{msg}] Stack size differs! Expected: {len(result)} Actual: {stack.Count}"

    for i, (expected_item, actual_item) in enumerate(zip(result, reversed(stack.Items))):
        prepared_testvector = prepare_testvector(expected_item)
        prepared_item = prepare_stackitem(actual_item)
        assert prepared_item == prepared_testvector, f"[{msg}] Stack item differs! Expected: {prepared_testvector} Actual: {prepared_item}"


def prepare_testvector(item):
    itype = item['type']
    if itype in ["Array", "Struct"]:
        new_value = []
        for entry in item['value']:
            new_value.append(prepare_testvector(entry))
        return (itype, new_value)
    elif itype == "Boolean":
        return (itype, item['value'])
    elif itype == "ByteArray":
        value = bytearray.fromhex(item['value'][2:])
        return (itype, value)
    elif itype == "Integer":
        return (itype, int(item['value']))
    elif itype == "Interop":
        return (itype, item['value'])
    elif itype == "Map":
        return (itype, item['value'])
    else:
        raise Exception(f"No handling for type: {itype}")


def prepare_stackitem(item):
    if isinstance(item, InteropService.Struct):
        # has to come before Array as it subclasses Array, otherwise we'll tag it wrong
        new_value = []
        for i in item.GetArray():
            new_value.append(prepare_stackitem(i))
        return ("Struct", new_value)

    elif isinstance(item, InteropService.Array):
        new_value = []
        for i in item.GetArray():
            new_value.append(prepare_stackitem(i))
        return ("Array", new_value)
    elif isinstance(item, InteropService.Boolean):
        return ("Boolean", item.GetBoolean())
    elif isinstance(item, InteropService.ByteArray):
        return ("ByteArray", item.GetByteArray())
    elif isinstance(item, InteropService.Integer):
        return ("Integer", item.GetBigInteger())
    elif isinstance(item, InteropService.InteropInterface):
        obj = item.GetInterface()
        return ("Interop", obj.__class__.__name__)
    elif isinstance(item, InteropService.Map):
        # TODO: implement once there is a reference test case that does not return an empty dictionary
        return ("Map", {})
    else:
        raise Exception(f"No handling for type: {item}")


if __name__ == "__main__":
    # Note: running from main requires manually downloading the tests from the neo-vm project
    # and storing them in a folder in the root directory
    main()
