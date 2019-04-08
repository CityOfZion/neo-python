import hashlib
import datetime

from neo.VM.OpCode import *
from neo.VM.RandomAccessStack import RandomAccessStack
from neo.VM.ExecutionContext import ExecutionContext
from neo.VM import VMState
from neo.VM.InteropService import Array, Struct, CollectionMixin, Map, Boolean
from neo.Core.UInt160 import UInt160
from neo.Settings import settings
from neo.VM.VMFault import VMFault
from neo.Prompt.vm_debugger import VMDebugger
from logging import DEBUG as LOGGING_LEVEL_DEBUG
from neo.logging import log_manager
from typing import TYPE_CHECKING
from collections import deque

if TYPE_CHECKING:
    from neo.VM.InteropService import BigInteger

logger = log_manager.getLogger('vm')

int_MaxValue = 2147483647


class ExecutionEngine:
    log_file_name = 'vm_instructions.log'
    # file descriptor
    log_file = None
    _vm_debugger = None

    MaxSizeForBigInteger = 32
    max_shl_shr = 65535  # ushort.maxValue
    min_shl_shr = -65535  # -ushort.maxValue
    maxItemSize = 1024 * 1024
    maxArraySize = 1024
    maxStackSize = 2048
    maxInvocationStackSize = 1024

    def __init__(self, container=None, crypto=None, table=None, service=None, exit_on_error=False):
        self._VMState = VMState.BREAK
        self._ScriptContainer = container
        self._Crypto = crypto
        self._Table = table
        self._Service = service
        self._exit_on_error = exit_on_error
        self._InvocationStack = RandomAccessStack(name='Invocation')
        self._ResultStack = RandomAccessStack(name='Result')
        self._ExecutedScriptHashes = []
        self.ops_processed = 0
        self._debug_map = None
        self._is_write_log = settings.log_vm_instructions
        self._breakpoints = dict()
        self._is_stackitem_count_strict = True
        self._stackitem_count = 0

    def CheckArraySize(self, length: int) -> bool:
        return length <= self.maxArraySize

    def CheckMaxItemSize(self, length: int) -> bool:
        return length >= 0 and length <= self.maxItemSize

    def CheckMaxInvocationStack(self) -> bool:
        return self.InvocationStack.Count < self.maxInvocationStackSize

    def CheckBigInteger(self, value: 'BigInteger') -> bool:
        return len(value.ToByteArray()) <= self.MaxSizeForBigInteger

    def CheckBigIntegerByteLength(self, byteLength: int) -> bool:
        return byteLength <= self.MaxSizeForBigInteger

    def CheckShift(self, shift: int) -> bool:
        return shift <= self.max_shl_shr and shift >= self.min_shl_shr

    def CheckStackSize(self, strict: bool, count: int = 1) -> bool:
        self._is_stackitem_count_strict &= strict
        self._stackitem_count += count

        # the C# implementation expects to overflow a signed int into negative when supplying a count of int.MaxValue so we check for exceeding int.MaxValue
        if self._stackitem_count < 0 or self._stackitem_count > int_MaxValue:
            self._stackitem_count = int_MaxValue

        if self._stackitem_count <= self.maxStackSize:
            return True

        if self._is_stackitem_count_strict:
            return False

        stack_item_list = []
        for execution_context in self.InvocationStack.Items:  # type: ExecutionContext
            stack_item_list += execution_context.EvaluationStack.Items + execution_context.AltStack.Items

        self._stackitem_count = self.GetItemCount(stack_item_list)
        if self._stackitem_count > self.maxStackSize:
            return False

        self._is_stackitem_count_strict = True
        return True

    def GetItemCount(self, items_list):  # list of StackItems
        count = 0
        items = deque(items_list)
        while items:
            stackitem = items.pop()
            if isinstance(stackitem, Map):
                items.extend(stackitem.Values)
                continue

            if isinstance(stackitem, Array):
                items.extend(stackitem.GetArray())
                continue
            count += 1

        return count

    def write_log(self, message):
        """
        Write a line to the VM instruction log file.

        Args:
            message (str): string message to write to file.
        """
        if self._is_write_log and self.log_file and not self.log_file.closed:
            self.log_file.write(message + '\n')

    @property
    def ScriptContainer(self):
        return self._ScriptContainer

    @property
    def Crypto(self):
        return self._Crypto

    @property
    def State(self):
        return self._VMState

    @property
    def InvocationStack(self):
        return self._InvocationStack

    @property
    def ResultStack(self):
        return self._ResultStack

    @property
    def CurrentContext(self) -> ExecutionContext:
        return self._InvocationStack.Peek()

    @property
    def CallingContext(self):
        if self._InvocationStack.Count > 1:
            return self.InvocationStack.Peek(1)
        return None

    @property
    def ExitOnError(self):
        return self._exit_on_error

    @property
    def EntryContext(self):
        return self.InvocationStack.Peek(self.InvocationStack.Count - 1)

    @property
    def ExecutedScriptHashes(self):
        return self._ExecutedScriptHashes

    def AddBreakPoint(self, script_hash, position):
        ctx_breakpoints = self._breakpoints.get(script_hash, None)
        if ctx_breakpoints is None:
            self._breakpoints[script_hash] = set([position])
        else:
            # add by reference
            ctx_breakpoints.add(position)

    def LoadDebugInfoForScriptHash(self, debug_map, script_hash):
        if debug_map and script_hash:
            self._debug_map = debug_map
            self._debug_map['script_hash'] = script_hash

    def Dispose(self):
        while self._InvocationStack.Count > 0:
            self._InvocationStack.Pop().Dispose()

    def Execute(self):
        self._VMState &= ~VMState.BREAK

        def loop_stepinto():
            while self._VMState & VMState.HALT == 0 and self._VMState & VMState.FAULT == 0 and self._VMState & VMState.BREAK == 0:
                self.ExecuteNext()

        if settings.log_vm_instructions:
            with open(self.log_file_name, 'w') as self.log_file:
                self.write_log(str(datetime.datetime.now()))
                loop_stepinto()
        else:
            loop_stepinto()

    def ExecuteOp(self, opcode, context: ExecutionContext):
        estack = context._EvaluationStack
        istack = self._InvocationStack
        astack = context._AltStack

        if opcode >= PUSHBYTES1 and opcode <= PUSHBYTES75:
            bytestoread = context.OpReader.SafeReadBytes(int.from_bytes(opcode, 'little'))
            estack.PushT(bytestoread)

            if not self.CheckStackSize(True):
                return self.VM_FAULT_and_report(VMFault.INVALID_STACKSIZE)
        else:

            # push values
            pushops = [PUSHM1, PUSH1, PUSH2, PUSH3, PUSH4, PUSH5, PUSH6, PUSH7, PUSH8,
                       PUSH9, PUSH10, PUSH11, PUSH12, PUSH13, PUSH14, PUSH15, PUSH16]

            if opcode == PUSH0:
                estack.PushT(bytearray(0))
                if not self.CheckStackSize(True):
                    return self.VM_FAULT_and_report(VMFault.INVALID_STACKSIZE)

            elif opcode == PUSHDATA1:
                lenngth = ord(context.OpReader.ReadByte())
                estack.PushT(bytearray(context.OpReader.SafeReadBytes(lenngth)))

                if not self.CheckStackSize(True):
                    return self.VM_FAULT_and_report(VMFault.INVALID_STACKSIZE)

            elif opcode == PUSHDATA2:
                estack.PushT(context.OpReader.SafeReadBytes(context.OpReader.ReadUInt16()))

                if not self.CheckStackSize(True):
                    return self.VM_FAULT_and_report(VMFault.INVALID_STACKSIZE)

            elif opcode == PUSHDATA4:
                length = context.OpReader.ReadUInt32()
                if not self.CheckMaxItemSize(length):
                    return self.VM_FAULT_and_report(VMFault.PUSHDATA_EXCEED_MAXITEMSIZE)

                estack.PushT(context.OpReader.SafeReadBytes(length))

                if not self.CheckStackSize(True):
                    return self.VM_FAULT_and_report(VMFault.INVALID_STACKSIZE)

            elif opcode in pushops:
                topush = int.from_bytes(opcode, 'little') - int.from_bytes(PUSH1, 'little') + 1
                estack.PushT(topush)

                if not self.CheckStackSize(True):
                    return self.VM_FAULT_and_report(VMFault.INVALID_STACKSIZE)

            # control
            elif opcode == NOP:
                pass
            elif opcode in [JMP, JMPIF, JMPIFNOT]:
                offset_b = context.OpReader.ReadInt16()
                offset = context.InstructionPointer + offset_b - 3

                if offset < 0 or offset > len(context.Script):
                    return self.VM_FAULT_and_report(VMFault.INVALID_JUMP)

                fValue = True
                if opcode > JMP:
                    self.CheckStackSize(False, -1)
                    fValue = estack.Pop().GetBoolean()
                    if opcode == JMPIFNOT:
                        fValue = not fValue
                if fValue:
                    context.SetInstructionPointer(offset)

            elif opcode == CALL:
                if not self.CheckMaxInvocationStack():
                    return self.VM_FAULT_and_report(VMFault.CALL_EXCEED_MAX_INVOCATIONSTACK_SIZE)

                context_call = self.LoadScript(context.Script)
                context.EvaluationStack.CopyTo(context_call.EvaluationStack)
                context_call.InstructionPointer = context.InstructionPointer
                context.EvaluationStack.Clear()
                context.InstructionPointer += 2

                self.ExecuteOp(JMP, context_call)

            elif opcode == RET:
                context_pop: ExecutionContext = istack.Pop()
                rvcount = context_pop._RVCount

                if rvcount == -1:
                    rvcount = context_pop.EvaluationStack.Count

                if rvcount > 0:
                    if context_pop.EvaluationStack.Count < rvcount:
                        return self.VM_FAULT_and_report(VMFault.UNKNOWN1)

                    if istack.Count == 0:
                        stack_eval = self._ResultStack
                    else:
                        stack_eval = self.CurrentContext.EvaluationStack
                    context_pop.EvaluationStack.CopyTo(stack_eval, rvcount)

                if context_pop._RVCount == -1 and istack.Count > 0:
                    context_pop.AltStack.CopyTo(self.CurrentContext.AltStack)

                self.CheckStackSize(False, 0)

                if istack.Count == 0:
                    self._VMState = VMState.HALT

            elif opcode == APPCALL or opcode == TAILCALL:
                if self._Table is None:
                    return self.VM_FAULT_and_report(VMFault.UNKNOWN2)

                if opcode == APPCALL and not self.CheckMaxInvocationStack():
                    return self.VM_FAULT_and_report(VMFault.APPCALL_EXCEED_MAX_INVOCATIONSTACK_SIZE)

                script_hash = context.OpReader.SafeReadBytes(20)

                is_normal_call = False
                for b in script_hash:
                    if b > 0:
                        is_normal_call = True

                if not is_normal_call:
                    script_hash = estack.Pop().GetByteArray()

                script = self._Table.GetScript(UInt160(data=script_hash).ToBytes())

                if script is None:
                    return self.VM_FAULT_and_report(VMFault.INVALID_CONTRACT, script_hash)

                context_new = self.LoadScript(script)
                estack.CopyTo(context_new.EvaluationStack)

                if opcode == TAILCALL:
                    istack.Remove(1).Dispose()
                else:
                    estack.Clear()

                self.CheckStackSize(False, 0)

            elif opcode == SYSCALL:
                try:
                    call = context.OpReader.ReadVarBytes(252).decode('ascii')
                except ValueError:
                    # probably failed to read enough bytes
                    return self.VM_FAULT_and_report(VMFault.SYSCALL_INSUFFICIENT_DATA)

                self.write_log(call)
                if not self._Service.Invoke(call, self):
                    return self.VM_FAULT_and_report(VMFault.SYSCALL_ERROR, call)

                if not self.CheckStackSize(False, int_MaxValue):
                    return self.VM_FAULT_and_report(VMFault.INVALID_STACKSIZE)

            # stack operations
            elif opcode == DUPFROMALTSTACK:
                estack.PushT(astack.Peek())

                if not self.CheckStackSize(True):
                    return self.VM_FAULT_and_report(VMFault.INVALID_STACKSIZE)

            elif opcode == TOALTSTACK:
                astack.PushT(estack.Pop())

            elif opcode == FROMALTSTACK:
                estack.PushT(astack.Pop())

            elif opcode == XDROP:
                n = estack.Pop().GetBigInteger()
                if n < 0:
                    self._VMState = VMState.FAULT
                    return
                estack.Remove(n)
                self.CheckStackSize(False, -2)

            elif opcode == XSWAP:
                n = estack.Pop().GetBigInteger()

                if n < 0:
                    return self.VM_FAULT_and_report(VMFault.UNKNOWN3)

                self.CheckStackSize(True, -1)

                # if n == 0 break, same as do x if n > 0
                if n > 0:
                    item = estack.Peek(n)
                    estack.Set(n, estack.Peek())
                    estack.Set(0, item)

            elif opcode == XTUCK:
                n = estack.Pop().GetBigInteger()

                if n <= 0:
                    return self.VM_FAULT_and_report(VMFault.UNKNOWN4)

                estack.Insert(n, estack.Peek())

            elif opcode == DEPTH:
                estack.PushT(estack.Count)
                if not self.CheckStackSize(True):
                    return self.VM_FAULT_and_report(VMFault.INVALID_STACKSIZE)

            elif opcode == DROP:
                estack.Pop()
                self.CheckStackSize(False, -1)

            elif opcode == DUP:
                estack.PushT(estack.Peek())
                if not self.CheckStackSize(True):
                    return self.VM_FAULT_and_report(VMFault.INVALID_STACKSIZE)

            elif opcode == NIP:
                estack.Remove(1)
                self.CheckStackSize(False, -1)

            elif opcode == OVER:
                estack.PushT(estack.Peek(1))
                if not self.CheckStackSize(True):
                    return self.VM_FAULT_and_report(VMFault.INVALID_STACKSIZE)

            elif opcode == PICK:

                n = estack.Pop().GetBigInteger()
                if n < 0:
                    return self.VM_FAULT_and_report(VMFault.UNKNOWN5)

                estack.PushT(estack.Peek(n))

            elif opcode == ROLL:

                n = estack.Pop().GetBigInteger()
                if n < 0:
                    return self.VM_FAULT_and_report(VMFault.UNKNOWN6)
                self.CheckStackSize(True, -1)

                if n > 0:
                    estack.PushT(estack.Remove(n))

            elif opcode == ROT:
                estack.PushT(estack.Remove(2))

            elif opcode == SWAP:
                estack.PushT(estack.Remove(1))

            elif opcode == TUCK:
                estack.Insert(2, estack.Peek())
                if not self.CheckStackSize(True):
                    return self.VM_FAULT_and_report(VMFault.INVALID_STACKSIZE)

            elif opcode == CAT:

                x2 = estack.Pop().GetByteArray()
                x1 = estack.Pop().GetByteArray()
                if not self.CheckMaxItemSize(len(x1) + len(x2)):
                    return self.VM_FAULT_and_report(VMFault.CAT_EXCEED_MAXITEMSIZE)
                estack.PushT(x1 + x2)
                self.CheckStackSize(True, -1)

            elif opcode == SUBSTR:

                count = estack.Pop().GetBigInteger()
                if count < 0:
                    return self.VM_FAULT_and_report(VMFault.SUBSTR_INVALID_LENGTH)

                index = estack.Pop().GetBigInteger()
                if index < 0:
                    return self.VM_FAULT_and_report(VMFault.SUBSTR_INVALID_INDEX)

                x = estack.Pop().GetByteArray()

                estack.PushT(x[index:count + index])
                self.CheckStackSize(True, -2)

            elif opcode == LEFT:

                count = estack.Pop().GetBigInteger()
                if count < 0:
                    return self.VM_FAULT_and_report(VMFault.LEFT_INVALID_COUNT)

                x = estack.Pop().GetByteArray()
                estack.PushT(x[:count])
                self.CheckStackSize(True, -1)

            elif opcode == RIGHT:

                count = estack.Pop().GetBigInteger()
                if count < 0:
                    return self.VM_FAULT_and_report(VMFault.RIGHT_INVALID_COUNT)

                x = estack.Pop().GetByteArray()
                if len(x) < count:
                    return self.VM_FAULT_and_report(VMFault.RIGHT_UNKNOWN)

                estack.PushT(x[-count:])
                self.CheckStackSize(True, -1)

            elif opcode == SIZE:

                x = estack.Pop().GetByteArray()
                estack.PushT(len(x))

            elif opcode == INVERT:

                x = estack.Pop().GetBigInteger()
                estack.PushT(~x)

            elif opcode == AND:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()
                estack.PushT(x1 & x2)
                self.CheckStackSize(True, -1)

            elif opcode == OR:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(x1 | x2)
                self.CheckStackSize(True, -1)

            elif opcode == XOR:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(x1 ^ x2)
                self.CheckStackSize(True, -1)

            elif opcode == EQUAL:
                x2 = estack.Pop()
                x1 = estack.Pop()
                estack.PushT(x1.Equals(x2))
                self.CheckStackSize(False, -1)

            # numeric
            elif opcode == INC:

                x = estack.Pop().GetBigInteger()
                if not self.CheckBigInteger(x) or not self.CheckBigInteger(x + 1):
                    return self.VM_FAULT_and_report(VMFault.BIGINTEGER_EXCEED_LIMIT)
                estack.PushT(x + 1)

            elif opcode == DEC:

                x = estack.Pop().GetBigInteger()  # type: BigInteger
                if not self.CheckBigInteger(x) or (x.Sign <= 0 and not self.CheckBigInteger(x - 1)):
                    return self.VM_FAULT_and_report(VMFault.BIGINTEGER_EXCEED_LIMIT)

                estack.PushT(x - 1)

            elif opcode == SIGN:

                # Make sure to implement sign for big integer
                x = estack.Pop().GetBigInteger()
                estack.PushT(x.Sign)

            elif opcode == NEGATE:

                x = estack.Pop().GetBigInteger()
                estack.PushT(-x)

            elif opcode == ABS:

                x = estack.Pop().GetBigInteger()
                estack.PushT(abs(x))

            elif opcode == NOT:

                x = estack.Pop().GetBigInteger()
                estack.PushT(not x)
                self.CheckStackSize(False, 0)

            elif opcode == NZ:

                x = estack.Pop().GetBigInteger()
                estack.PushT(x is not 0)

            elif opcode == ADD:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()
                if not self.CheckBigInteger(x1) or not self.CheckBigInteger(x2) or not self.CheckBigInteger(x1 + x2):
                    return self.VM_FAULT_and_report(VMFault.BIGINTEGER_EXCEED_LIMIT)

                estack.PushT(x1 + x2)
                self.CheckStackSize(True, -1)

            elif opcode == SUB:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()
                if not self.CheckBigInteger(x1) or not self.CheckBigInteger(x2) or not self.CheckBigInteger(x1 - x2):
                    return self.VM_FAULT_and_report(VMFault.BIGINTEGER_EXCEED_LIMIT)

                estack.PushT(x1 - x2)
                self.CheckStackSize(True, -1)

            elif opcode == MUL:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()  # type: BigInteger
                len_x1 = len(x1.ToByteArray())

                if not self.CheckBigIntegerByteLength(len_x1):
                    return self.VM_FAULT_and_report(VMFault.BIGINTEGER_EXCEED_LIMIT)

                len_x2 = len(x2.ToByteArray())
                if not self.CheckBigIntegerByteLength(len_x1 + len_x2):
                    return self.VM_FAULT_and_report(VMFault.BIGINTEGER_EXCEED_LIMIT)
                estack.PushT(x1 * x2)
                self.CheckStackSize(True, -1)

            elif opcode == DIV:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()
                if not self.CheckBigInteger(x1) or not self.CheckBigInteger(x2):
                    return self.VM_FAULT_and_report(VMFault.BIGINTEGER_EXCEED_LIMIT)

                estack.PushT(x1 / x2)
                self.CheckStackSize(True, -1)

            elif opcode == MOD:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(x1 % x2)
                self.CheckStackSize(True, -1)

            elif opcode == SHL:

                shift = estack.Pop().GetBigInteger()
                if not self.CheckShift(shift):
                    return self.VM_FAULT_and_report(VMFault.INVALID_SHIFT)

                x = estack.Pop().GetBigInteger()

                if not self.CheckBigInteger(x):
                    return self.VM_FAULT_and_report(VMFault.BIGINTEGER_EXCEED_LIMIT)

                x = x << shift

                if not self.CheckBigInteger(x):
                    return self.VM_FAULT_and_report(VMFault.BIGINTEGER_EXCEED_LIMIT)

                estack.PushT(x)
                self.CheckStackSize(True, -1)

            elif opcode == SHR:

                shift = estack.Pop().GetBigInteger()
                if not self.CheckShift(shift):
                    return self.VM_FAULT_and_report(VMFault.INVALID_SHIFT)

                x = estack.Pop().GetBigInteger()

                if not self.CheckBigInteger(x):
                    return self.VM_FAULT_and_report(VMFault.BIGINTEGER_EXCEED_LIMIT)

                estack.PushT(x >> shift)
                self.CheckStackSize(True, -1)

            elif opcode == BOOLAND:

                x2 = estack.Pop().GetBoolean()
                x1 = estack.Pop().GetBoolean()

                estack.PushT(x1 and x2)
                self.CheckStackSize(False, -1)

            elif opcode == BOOLOR:

                x2 = estack.Pop().GetBoolean()
                x1 = estack.Pop().GetBoolean()

                estack.PushT(x1 or x2)
                self.CheckStackSize(False, -1)

            elif opcode == NUMEQUAL:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(x2 == x1)
                self.CheckStackSize(True, -1)

            elif opcode == NUMNOTEQUAL:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(x1 != x2)
                self.CheckStackSize(True, -1)

            elif opcode == LT:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(x1 < x2)
                self.CheckStackSize(True, -1)

            elif opcode == GT:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(x1 > x2)
                self.CheckStackSize(True, -1)

            elif opcode == LTE:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(x1 <= x2)
                self.CheckStackSize(True, -1)

            elif opcode == GTE:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(x1 >= x2)
                self.CheckStackSize(True, -1)

            elif opcode == MIN:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()
                estack.PushT(min(x1, x2))
                self.CheckStackSize(True, -1)

            elif opcode == MAX:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(max(x1, x2))
                self.CheckStackSize(True, -1)

            elif opcode == WITHIN:

                b = estack.Pop().GetBigInteger()
                a = estack.Pop().GetBigInteger()
                x = estack.Pop().GetBigInteger()

                estack.PushT(a <= x and x < b)
                self.CheckStackSize(True, -2)

            # CRyPTO
            elif opcode == SHA1:
                h = hashlib.sha1(estack.Pop().GetByteArray())
                estack.PushT(h.digest())

            elif opcode == SHA256:
                h = hashlib.sha256(estack.Pop().GetByteArray())
                estack.PushT(h.digest())

            elif opcode == HASH160:

                estack.PushT(self.Crypto.Hash160(estack.Pop().GetByteArray()))

            elif opcode == HASH256:

                estack.PushT(self.Crypto.Hash256(estack.Pop().GetByteArray()))

            elif opcode == CHECKSIG:

                pubkey = estack.Pop().GetByteArray()
                sig = estack.Pop().GetByteArray()
                container = self.ScriptContainer
                if not container:
                    logger.debug("Cannot check signature without container")
                    estack.PushT(False)
                    return
                try:
                    res = self.Crypto.VerifySignature(container.GetMessage(), sig, pubkey)
                    estack.PushT(res)
                except Exception as e:
                    estack.PushT(False)
                    logger.debug("Could not checksig: %s " % e)
                self.CheckStackSize(True, -1)

            elif opcode == VERIFY:
                pubkey = estack.Pop().GetByteArray()
                sig = estack.Pop().GetByteArray()
                message = estack.Pop().GetByteArray()
                try:
                    res = self.Crypto.VerifySignature(message, sig, pubkey, unhex=False)
                    estack.PushT(res)
                except Exception as e:
                    estack.PushT(False)
                    logger.debug("Could not verify: %s " % e)
                self.CheckStackSize(True, -2)

            elif opcode == CHECKMULTISIG:
                item = estack.Pop()
                pubkeys = []

                if isinstance(item, Array):

                    for p in item.GetArray():
                        pubkeys.append(p.GetByteArray())
                    n = len(pubkeys)
                    if n == 0:
                        return self.VM_FAULT_and_report(VMFault.CHECKMULTISIG_INVALID_PUBLICKEY_COUNT)

                    self.CheckStackSize(False, -1)
                else:
                    n = item.GetBigInteger()

                    if n < 1 or n > estack.Count:
                        return self.VM_FAULT_and_report(VMFault.CHECKMULTISIG_INVALID_PUBLICKEY_COUNT)

                    for i in range(0, n):
                        pubkeys.append(estack.Pop().GetByteArray())
                    self.CheckStackSize(True, -n - 1)

                item = estack.Pop()
                sigs = []

                if isinstance(item, Array):
                    for s in item.GetArray():
                        sigs.append(s.GetByteArray())
                    m = len(sigs)

                    if m == 0 or m > n:
                        return self.VM_FAULT_and_report(VMFault.CHECKMULTISIG_SIGNATURE_ERROR, m, n)
                    self.CheckStackSize(False, -1)
                else:
                    m = item.GetBigInteger()

                    if m < 1 or m > n or m > estack.Count:
                        return self.VM_FAULT_and_report(VMFault.CHECKMULTISIG_SIGNATURE_ERROR, m, n)

                    for i in range(0, m):
                        sigs.append(estack.Pop().GetByteArray())
                    self.CheckStackSize(True, -m - 1)

                message = self.ScriptContainer.GetMessage() if self.ScriptContainer else ''

                fSuccess = True

                try:

                    i = 0
                    j = 0

                    while fSuccess and i < m and j < n:

                        if self.Crypto.VerifySignature(message, sigs[i], pubkeys[j]):
                            i += 1
                        j += 1

                        if m - i > n - j:
                            fSuccess = False

                except Exception as e:
                    fSuccess = False

                estack.PushT(fSuccess)

            # lists
            elif opcode == ARRAYSIZE:

                item = estack.Pop()

                if not item:
                    return self.VM_FAULT_and_report(VMFault.UNKNOWN7)

                if isinstance(item, CollectionMixin):
                    estack.PushT(item.Count)
                    self.CheckStackSize(False, 0)

                else:
                    estack.PushT(len(item.GetByteArray()))
                    self.CheckStackSize(True, 0)

            elif opcode == PACK:

                size = estack.Pop().GetBigInteger()

                if size < 0 or size > estack.Count or not self.CheckArraySize(size):
                    return self.VM_FAULT_and_report(VMFault.UNKNOWN8)

                items = []

                for i in range(0, size):
                    topack = estack.Pop()
                    items.append(topack)

                estack.PushT(items)

            elif opcode == UNPACK:
                item = estack.Pop()

                if not isinstance(item, Array):
                    return self.VM_FAULT_and_report(VMFault.UNPACK_INVALID_TYPE, item)

                items = item.GetArray()
                items.reverse()

                [estack.PushT(i) for i in items]

                estack.PushT(len(items))
                if not self.CheckStackSize(False, len(items)):
                    self.VM_FAULT_and_report(VMFault.INVALID_STACKSIZE)

            elif opcode == PICKITEM:

                key = estack.Pop()

                if isinstance(key, CollectionMixin):
                    # key must be an array index or dictionary key, but not a collection
                    return self.VM_FAULT_and_report(VMFault.KEY_IS_COLLECTION, key)

                collection = estack.Pop()

                if isinstance(collection, Array):
                    index = key.GetBigInteger()
                    if index < 0 or index >= collection.Count:
                        return self.VM_FAULT_and_report(VMFault.PICKITEM_INVALID_INDEX, index, collection.Count)

                    items = collection.GetArray()
                    to_pick = items[index]
                    estack.PushT(to_pick)

                    if not self.CheckStackSize(False, int_MaxValue):
                        self.VM_FAULT_and_report(VMFault.INVALID_STACKSIZE)

                elif isinstance(collection, Map):
                    success, value = collection.TryGetValue(key)

                    if success:
                        estack.PushT(value)

                        if not self.CheckStackSize(False, int_MaxValue):
                            self.VM_FAULT_and_report(VMFault.INVALID_STACKSIZE)

                    else:
                        return self.VM_FAULT_and_report(VMFault.DICT_KEY_NOT_FOUND, key, collection.Keys)
                else:
                    byte_array = collection.GetByteArray()
                    index = key.GetBigInteger()
                    if index < 0 or index >= len(byte_array):
                        self.VM_FAULT_and_report(VMFault.PICKITEM_INVALID_INDEX, index, len(byte_array))
                        return
                    estack.PushT(byte_array[index])
                    self.CheckStackSize(False, -1)

            elif opcode == SETITEM:
                value = estack.Pop()

                if isinstance(value, Struct):
                    value = value.Clone()

                key = estack.Pop()

                if isinstance(key, CollectionMixin):
                    return self.VM_FAULT_and_report(VMFault.KEY_IS_COLLECTION)

                collection = estack.Pop()

                if isinstance(collection, Array):

                    index = key.GetBigInteger()

                    if index < 0 or index >= collection.Count:
                        return self.VM_FAULT_and_report(VMFault.SETITEM_INVALID_INDEX)

                    items = collection.GetArray()
                    items[index] = value

                elif isinstance(collection, Map):
                    if not collection.ContainsKey(key) and not self.CheckArraySize(collection.Count + 1):
                        return self.VM_FAULT_and_report(VMFault.SETITEM_INVALID_MAP)

                    collection.SetItem(key, value)

                else:
                    return self.VM_FAULT_and_report(VMFault.SETITEM_INVALID_TYPE, key, collection)

                if not self.CheckStackSize(False, int_MaxValue):
                    self.VM_FAULT_and_report(VMFault.INVALID_STACKSIZE)

            elif opcode in [NEWARRAY, NEWSTRUCT]:
                item = estack.Pop()
                if isinstance(item, Array):
                    result = None
                    if isinstance(item, Struct):
                        if opcode == NEWSTRUCT:
                            result = item
                    else:
                        if opcode == NEWARRAY:
                            result = item

                    if result is None:
                        result = Array(item) if opcode == NEWARRAY else Struct(item)

                    estack.PushT(result)

                else:
                    count = item.GetBigInteger()
                    if count < 0:
                        return self.VM_FAULT_and_report(VMFault.NEWARRAY_NEGATIVE_COUNT)

                    if not self.CheckArraySize(count):
                        return self.VM_FAULT_and_report(VMFault.NEWARRAY_EXCEED_ARRAYLIMIT)

                    items = [Boolean(False) for i in range(0, count)]

                    result = Array(items) if opcode == NEWARRAY else Struct(items)

                    estack.PushT(result)

                    if not self.CheckStackSize(True, count):
                        self.VM_FAULT_and_report(VMFault.INVALID_STACKSIZE)

            elif opcode == NEWMAP:
                estack.PushT(Map())
                if not self.CheckStackSize(True):
                    self.VM_FAULT_and_report(VMFault.INVALID_STACKSIZE)

            elif opcode == APPEND:
                newItem = estack.Pop()

                if isinstance(newItem, Struct):
                    newItem = newItem.Clone()

                arrItem = estack.Pop()

                if not isinstance(arrItem, Array):
                    return self.VM_FAULT_and_report(VMFault.APPEND_INVALID_TYPE, arrItem)

                arr = arrItem.GetArray()
                if not self.CheckArraySize(len(arr) + 1):
                    return self.VM_FAULT_and_report(VMFault.APPEND_EXCEED_ARRAYLIMIT)
                arr.append(newItem)

                if not self.CheckStackSize(False, int_MaxValue):
                    self.VM_FAULT_and_report(VMFault.INVALID_STACKSIZE)

            elif opcode == REVERSE:

                arrItem = estack.Pop()
                self.CheckStackSize(False, -1)

                if not isinstance(arrItem, Array):
                    return self.VM_FAULT_and_report(VMFault.REVERSE_INVALID_TYPE, arrItem)

                arrItem.Reverse()

            elif opcode == REMOVE:

                key = estack.Pop()

                if isinstance(key, CollectionMixin):
                    return self.VM_FAULT_and_report(VMFault.UNKNOWN1)

                collection = estack.Pop()
                self.CheckStackSize(False, -2)

                if isinstance(collection, Array):

                    index = key.GetBigInteger()

                    if index < 0 or index >= collection.Count:
                        return self.VM_FAULT_and_report(VMFault.REMOVE_INVALID_INDEX, index, collection.Count)

                    collection.RemoveAt(index)

                elif isinstance(collection, Map):

                    collection.Remove(key)

                else:

                    return self.VM_FAULT_and_report(VMFault.REMOVE_INVALID_TYPE, key, collection)

            elif opcode == HASKEY:

                key = estack.Pop()

                if isinstance(key, CollectionMixin):
                    return self.VM_FAULT_and_report(VMFault.DICT_KEY_ERROR)

                collection = estack.Pop()

                if isinstance(collection, Array):

                    index = key.GetBigInteger()

                    if index < 0:
                        return self.VM_FAULT_and_report(VMFault.DICT_KEY_ERROR)

                    estack.PushT(index < collection.Count)

                elif isinstance(collection, Map):

                    estack.PushT(collection.ContainsKey(key))

                else:

                    return self.VM_FAULT_and_report(VMFault.DICT_KEY_ERROR)
                self.CheckStackSize(False, -1)

            elif opcode == KEYS:

                collection = estack.Pop()

                if isinstance(collection, Map):

                    estack.PushT(Array(collection.Keys))
                    if not self.CheckStackSize(False, collection.Count):
                        self.VM_FAULT_and_report(VMFault.INVALID_STACKSIZE)
                else:
                    return self.VM_FAULT_and_report(VMFault.DICT_KEY_ERROR)

            elif opcode == VALUES:

                collection = estack.Pop()
                values = []

                if isinstance(collection, Map):
                    values = collection.Values

                elif isinstance(collection, Array):
                    values = collection

                else:
                    return self.VM_FAULT_and_report(VMFault.DICT_KEY_ERROR)

                newArray = Array()
                for item in values:
                    if isinstance(item, Struct):
                        newArray.Add(item.Clone())
                    else:
                        newArray.Add(item)

                estack.PushT(newArray)
                if not self.CheckStackSize(False, int_MaxValue):
                    self.VM_FAULT_and_report(VMFault.INVALID_STACKSIZE)

            # stack isolation
            elif opcode == CALL_I:
                if not self.CheckMaxInvocationStack():
                    return self.VM_FAULT_and_report(VMFault.CALL__I_EXCEED_MAX_INVOCATIONSTACK_SIZE)
                rvcount = ord(context.OpReader.ReadByte())
                pcount = ord(context.OpReader.ReadByte())

                if estack.Count < pcount:
                    return self.VM_FAULT_and_report(VMFault.UNKNOWN_STACKISOLATION)

                context_call = self.LoadScript(context.Script, rvcount)
                estack.CopyTo(context_call.EvaluationStack, pcount)
                context_call.InstructionPointer = context.InstructionPointer

                for i in range(0, pcount, 1):
                    estack.Pop()
                context.InstructionPointer += 2
                self.ExecuteOp(JMP, context_call)

            elif opcode in [CALL_E, CALL_ED, CALL_ET, CALL_EDT]:
                if self._Table is None:
                    return self.VM_FAULT_and_report(VMFault.UNKNOWN_STACKISOLATION2)

                rvcount = ord(context.OpReader.ReadByte())
                pcount = ord(context.OpReader.ReadByte())

                if estack.Count < pcount:
                    return self.VM_FAULT_and_report(VMFault.UNKNOWN_STACKISOLATION)

                if opcode in [CALL_ET, CALL_EDT]:
                    if context._RVCount != rvcount:
                        return self.VM_FAULT_and_report(VMFault.UNKNOWN_STACKISOLATION3)
                else:
                    if not self.CheckMaxInvocationStack():
                        return self.VM_FAULT_and_report(VMFault.UNKNOWN_EXCEED_MAX_INVOCATIONSTACK_SIZE)

                if opcode in [CALL_ED, CALL_EDT]:
                    script_hash = estack.Pop().GetByteArray()
                    self.CheckStackSize(True, -1)
                else:
                    script_hash = context.OpReader.SafeReadBytes(20)

                script = self._Table.GetScript(UInt160(data=script_hash).ToBytes())

                if script is None:
                    logger.debug("Could not find script from script table: %s " % script_hash)
                    return self.VM_FAULT_and_report(VMFault.INVALID_CONTRACT, script_hash)

                context_new = self.LoadScript(script, rvcount)
                estack.CopyTo(context_new.EvaluationStack, pcount)

                if opcode in [CALL_ET, CALL_EDT]:
                    istack.Remove(1).Dispose()
                else:
                    for i in range(0, pcount, 1):
                        estack.Pop()

            elif opcode == THROW:
                return self.VM_FAULT_and_report(VMFault.THROW)

            elif opcode == THROWIFNOT:
                if not estack.Pop().GetBoolean():
                    return self.VM_FAULT_and_report(VMFault.THROWIFNOT)
                self.CheckStackSize(False, -1)

            else:
                return self.VM_FAULT_and_report(VMFault.UNKNOWN_OPCODE, opcode)

    def LoadScript(self, script, rvcount=-1) -> ExecutionContext:

        context = ExecutionContext(self, script, rvcount)
        self._InvocationStack.PushT(context)
        self._ExecutedScriptHashes.append(context.ScriptHash())

        # add break points for current script if available
        script_hash = context.ScriptHash()
        if self._debug_map and script_hash == self._debug_map['script_hash']:
            self._breakpoints[script_hash] = set(self._debug_map['breakpoints'])

        return context

    def RemoveBreakPoint(self, script_hash, position):
        # test if any breakpoints exist for script hash
        ctx = self._breakpoints.get(script_hash, None)
        if ctx is None:
            return False

        # remove if specific bp exists
        if position in ctx:
            ctx.remove(position)
        else:
            return False

        # clear set from breakpoints list if no more bp's exist for it
        if len(ctx) == 0:
            del self._breakpoints[script_hash]

        return True

    def ExecuteNext(self):
        if self._InvocationStack.Count == 0:
            self._VMState = VMState.HALT
        else:
            op = None

            if self.CurrentContext.InstructionPointer >= len(self.CurrentContext.Script):
                op = RET
            else:
                op = self.CurrentContext.OpReader.ReadByte()

            self.ops_processed += 1

            try:
                if self._is_write_log:
                    self.write_log("{} {}".format(self.ops_processed, ToName(op)))
                self.ExecuteOp(op, self.CurrentContext)
            except Exception as e:
                error_msg = "COULD NOT EXECUTE OP (%s): %s %s %s" % (self.ops_processed, e, op, ToName(op))
                self.write_log(error_msg)

                if self._exit_on_error:
                    self._VMState = VMState.FAULT

            # This is how C# does it now (2019-03-25) according to
            # https://github.com/neo-project/neo-vm/blob/0e5cb856021e288915623fe994084d97a0417373/src/neo-vm/ExecutionEngine.cs#L234
            # but that doesn't help us set a breakpoint, so we use the old logic
            # TODO: revisit at some point
            # if self._VMState == VMState.NONE and self._InvocationStack.Count > 0:
            if self._VMState & VMState.FAULT == 0 and self._InvocationStack.Count > 0:
                script_hash = self.CurrentContext.ScriptHash()
                bps = self._breakpoints.get(self.CurrentContext.ScriptHash(), None)
                if bps is not None:
                    if self.CurrentContext.InstructionPointer in bps:
                        self._VMState = VMState.BREAK
                        self._vm_debugger = VMDebugger(self)
                        self._vm_debugger.start()

    def StepInto(self):

        if self._VMState & VMState.HALT > 0 or self._VMState & VMState.FAULT > 0:
            logger.debug("stopping because vm state is %s " % self._VMState)
            return
        self.ExecuteNext()
        if self._VMState == VMState.NONE:
            self._VMState = VMState.BREAK

    def VM_FAULT_and_report(self, id, *args):
        self._VMState = VMState.FAULT

        if not logger.hasHandlers() or logger.handlers[0].level != LOGGING_LEVEL_DEBUG:
            return

        # if settings.log_level != LOGGING_LEVEL_DEBUG:
        #     return

        if id == VMFault.INVALID_JUMP:
            error_msg = "Attemping to JMP/JMPIF/JMPIFNOT to an invalid location."

        elif id == VMFault.INVALID_CONTRACT:
            script_hash = args[0]
            error_msg = "Trying to call an unknown contract with script_hash {}\nMake sure the contract exists on the blockchain".format(script_hash)

        elif id == VMFault.CHECKMULTISIG_INVALID_PUBLICKEY_COUNT:
            error_msg = "CHECKMULTISIG - provided public key count is less than 1."

        elif id == VMFault.CHECKMULTISIG_SIGNATURE_ERROR:
            if args[0] < 1:
                error_msg = "CHECKMULTISIG - Minimum required signature count cannot be less than 1."
            else:  # m > n
                m = args[0]
                n = args[1]
                error_msg = "CHECKMULTISIG - Insufficient signatures provided ({}). Minimum required is {}".format(m, n)

        elif id == VMFault.UNPACK_INVALID_TYPE:
            item = args[0]
            error_msg = "Failed to UNPACK item. Item is not an array but of type: {}".format(type(item))

        elif id == VMFault.PICKITEM_INVALID_TYPE:
            index = args[0]
            item = args[1]
            error_msg = "Cannot access item at index {}. Item is not an array or dict but of type: {}".format(index, type(item))

        elif id == VMFault.PICKITEM_NEGATIVE_INDEX:
            error_msg = "Attempting to access an array using a negative index"

        elif id == VMFault.PICKITEM_INVALID_INDEX:
            index = args[0]
            length = args[1]
            error_msg = "Array index is less than zero or {} exceeds list length {}".format(index, length)

        elif id == VMFault.APPEND_INVALID_TYPE:
            item = args[0]
            error_msg = "Cannot append to item. Item is not an array but of type: {}".format(type(item))

        elif id == VMFault.REVERSE_INVALID_TYPE:
            item = args[0]
            error_msg = "Cannot REVERSE item. Item is not an array but of type: {}".format(type(item))

        elif id == VMFault.REMOVE_INVALID_TYPE:
            item = args[0]
            index = args[1]
            error_msg = "Cannot REMOVE item at index {}. Item is not an array but of type: {}".format(index, type(item))

        elif id == VMFault.REMOVE_INVALID_INDEX:
            index = args[0]
            length = args[1]

            if index < 0:
                error_msg = "Cannot REMOVE item at index {}. Index < 0".format(index)

            else:  # index >= len(items):
                error_msg = "Cannot REMOVE item at index {}. Index exceeds array length {}".format(index, length)

        elif id == VMFault.POP_ITEM_NOT_ARRAY:
            error_msg = "Items(s) not array: %s" % [item for item in args]

        elif id == VMFault.UNKNOWN_OPCODE:
            opcode = args[0]
            error_msg = "Unknown opcode found: {}".format(opcode)

        else:
            error_msg = id

        if id in [VMFault.THROW, VMFault.THROWIFNOT]:
            logger.debug("({}) {}".format(self.ops_processed, id))
        else:
            logger.debug("({}) {}".format(self.ops_processed, error_msg))

        return
