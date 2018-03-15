import hashlib
import pdb
import datetime

from logzero import logger
from neo.VM.RandomAccessStack import RandomAccessStack
from neo.VM.ExecutionContext import ExecutionContext
from neo.VM import VMState
from neo.VM.OpCode import *
from neo.VM.InteropService import Array, Struct, StackItem
from neocore.UInt160 import UInt160
from neo.Settings import settings
from neo.VM.VMFault import VMFault


class ExecutionEngine():
    _Table = None
    _Service = None

    _ScriptContainer = None
    _Crypto = None

    _VMState = VMState.BREAK

    _InvocationStack = None
    _EvaluationStack = None
    _AltStack = None

    _ExecutedScriptHashes = None

    ops_processed = 0

    _exit_on_error = False

    log_file_name = 'vm_instructions.log'
    # file descriptor
    log_file = None

    def write_log(self, message):
        """
        Write a line to the VM instruction log file.

        Args:
            message (str): string message to write to file.
        """
        if settings.log_vm_instructions and self.log_file and not self.log_file.closed:
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
    def EvaluationStack(self):
        return self._EvaluationStack

    @property
    def AltStack(self):
        return self._AltStack

    @property
    def CurrentContext(self):
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

    def __init__(self, container=None, crypto=None, table=None, service=None, exit_on_error=False):
        self._ScriptContainer = container
        self._Crypto = crypto
        self._Table = table
        self._Service = service
        self._exit_on_error = exit_on_error
        self._InvocationStack = RandomAccessStack(name='Invocation')
        self._EvaluationStack = RandomAccessStack(name='Evaluation')
        self._AltStack = RandomAccessStack(name='Alt')
        self._ExecutedScriptHashes = []
        self.ops_processed = 0

    def AddBreakPoint(self, position):
        self.CurrentContext.Breakpoints.add(position)

    def Dispose(self):
        while self._InvocationStack.Count > 0:
            self._InvocationStack.Pop().Dispose()

    def Execute(self):
        self._VMState &= ~VMState.BREAK

        def loop_stepinto():
            while self._VMState & VMState.HALT == 0 and self._VMState & VMState.FAULT == 0 and self._VMState & VMState.BREAK == 0:
                self.StepInto()

        if settings.log_vm_instructions:
            with open(self.log_file_name, 'w') as self.log_file:
                self.write_log(str(datetime.datetime.now()))
                loop_stepinto()
        else:
            loop_stepinto()

    def ExecuteOp(self, opcode, context):
        estack = self._EvaluationStack
        istack = self._InvocationStack
        astack = self._AltStack

        if opcode > PUSH16 and opcode != RET and context.PushOnly:
            return self.VM_FAULT_and_report(VMFault.UNKNOWN1)

        if opcode >= PUSHBYTES1 and opcode <= PUSHBYTES75:
            bytestoread = context.OpReader.ReadBytes(int.from_bytes(opcode, 'little'))
            estack.PushT(bytestoread)
        else:

            # push values
            pushops = [PUSHM1, PUSH1, PUSH2, PUSH3, PUSH4, PUSH5, PUSH6, PUSH7, PUSH8,
                       PUSH9, PUSH10, PUSH11, PUSH12, PUSH13, PUSH14, PUSH15, PUSH16]

            if opcode == PUSH0:
                estack.PushT(bytearray(0))

            elif opcode == PUSHDATA1:
                lenngth = context.OpReader.ReadByte()
                estack.PushT(bytearray(context.OpReader.ReadBytes(lenngth)))
            elif opcode == PUSHDATA2:
                estack.PushT(context.OpReader.ReadBytes(context.OpReader.ReadUInt16()))
            elif opcode == PUSHDATA4:
                estack.PushT(context.OpReader.ReadBytes(context.OpReader.ReadUInt32()))
            elif opcode in pushops:
                # EvaluationStack.Push((int)opcode - (int)OpCode.PUSH1 + 1);
                topush = int.from_bytes(opcode, 'little') - int.from_bytes(PUSH1, 'little') + 1
                estack.PushT(topush)

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
                    fValue = estack.Pop().GetBoolean()
                    if opcode == JMPIFNOT:
                        fValue = not fValue
                if fValue:
                    context.SetInstructionPointer(offset)

            elif opcode == CALL:
                istack.PushT(context.Clone())
                context.SetInstructionPointer(context.InstructionPointer + 2)

                self.ExecuteOp(JMP, self.CurrentContext)

            elif opcode == RET:
                istack.Pop().Dispose()
                if istack.Count == 0:
                    self._VMState |= VMState.HALT

            elif opcode == APPCALL or opcode == TAILCALL:
                if self._Table is None:
                    return self.VM_FAULT_and_report(VMFault.UNKNOWN2)

                script_hash = context.OpReader.ReadBytes(20)

                is_normal_call = False
                for b in script_hash:
                    if b > 0:
                        is_normal_call = True

                if not is_normal_call:
                    script_hash = self.EvaluationStack.Pop().GetByteArray()

                script = self._Table.GetScript(UInt160(data=script_hash).ToBytes())

                if script is None:
                    logger.error("Could not find script from script table: %s " % script_hash)
                    return self.VM_FAULT_and_report(VMFault.INVALID_CONTRACT, script_hash)

                if opcode == TAILCALL:
                    istack.Pop().Dispose()

                self.LoadScript(script)

            elif opcode == SYSCALL:
                call = context.OpReader.ReadVarBytes(252).decode('ascii')
                self.write_log(call)
                if not self._Service.Invoke(call, self):
                    return self.VM_FAULT_and_report(VMFault.SYSCALL_ERROR, call)

            # stack operations
            elif opcode == DUPFROMALTSTACK:
                estack.PushT(astack.Peek())

            elif opcode == TOALTSTACK:
                astack.PushT(estack.Pop())

            elif opcode == FROMALTSTACK:
                estack.PushT(astack.Pop())

            elif opcode == XDROP:
                n = estack.Pop().GetBigInteger()
                if n < 0:
                    self._VMState |= VMState.FAULT
                    return
                estack.Remove(n)

            elif opcode == XSWAP:
                n = estack.Pop().GetBigInteger()

                if n < 0:
                    return self.VM_FAULT_and_report(VMFault.UNKNOWN3)

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

            elif opcode == DROP:
                estack.Pop()

            elif opcode == DUP:
                estack.PushT(estack.Peek())

            elif opcode == NIP:
                x2 = estack.Pop()
                estack.Pop()
                estack.PushT(x2)

            elif opcode == OVER:

                x2 = estack.Pop()
                x1 = estack.Peek()
                estack.PushT(x2)
                estack.PushT(x1)

            elif opcode == PICK:

                n = estack.Pop().GetBigInteger()
                if n < 0:
                    return self.VM_FAULT_and_report(VMFault.UNKNOWN5)

                estack.PushT(estack.Peek(n))

            elif opcode == ROLL:

                n = estack.Pop().GetBigInteger()
                if n < 0:
                    return self.VM_FAULT_and_report(VMFault.UNKNOWN6)

                if n > 0:
                    estack.PushT(estack.Remove(n))

            elif opcode == ROT:
                x3 = estack.Pop()
                x2 = estack.Pop()
                x1 = estack.Pop()

                estack.PushT(x2)
                estack.PushT(x3)
                estack.PushT(x1)

            elif opcode == SWAP:

                x2 = estack.Pop()
                x1 = estack.Pop()
                estack.PushT(x2)
                estack.PushT(x1)

            elif opcode == TUCK:

                x2 = estack.Pop()
                x1 = estack.Pop()
                estack.PushT(x2)
                estack.PushT(x1)
                estack.PushT(x2)

            elif opcode == CAT:

                x2 = estack.Pop().GetByteArray()
                x1 = estack.Pop().GetByteArray()
                estack.PushT(x1 + x2)

            elif opcode == SUBSTR:

                count = estack.Pop().GetBigInteger()
                if count < 0:
                    return self.VM_FAULT_and_report(VMFault.SUBSTR_INVALID_LENGTH)

                index = estack.Pop().GetBigInteger()
                if index < 0:
                    return self.VM_FAULT_and_report(VMFault.SUBSTR_INVALID_INDEX)

                x = estack.Pop().GetByteArray()

                estack.PushT(x[index:count + index])

            elif opcode == LEFT:

                count = estack.Pop().GetBigInteger()
                if count < 0:
                    return self.VM_FAULT_and_report(VMFault.LEFT_INVALID_COUNT)

                x = estack.Pop().GetByteArray()
                estack.PushT(x[:count])

            elif opcode == RIGHT:

                count = estack.Pop().GetBigInteger()
                if count < 0:
                    return self.VM_FAULT_and_report(VMFault.RIGHT_INVALID_COUNT)

                x = estack.Pop().GetByteArray()
                if len(x) < count:
                    return self.VM_FAULT_and_report(VMFault.RIGHT_UNKNOWN)

                estack.PushT(x[-count:])

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

            elif opcode == OR:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(x1 | x2)

            elif opcode == XOR:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(x1 ^ x2)

            elif opcode == EQUAL:
                x2 = estack.Pop()
                x1 = estack.Pop()
                estack.PushT(x1.Equals(x2))

            # numeric

            elif opcode == INC:

                x = estack.Pop().GetBigInteger()
                estack.PushT(x + 1)

            elif opcode == DEC:

                x = estack.Pop().GetBigInteger()
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

            elif opcode == NZ:

                x = estack.Pop().GetBigInteger()
                estack.PushT(x is not 0)

            elif opcode == ADD:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()
                estack.PushT(x1 + x2)

            elif opcode == SUB:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(x1 - x2)

            elif opcode == MUL:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(x1 * x2)

            elif opcode == DIV:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(x1 / x2)

            elif opcode == MOD:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(x1 % x2)

            elif opcode == SHL:

                n = estack.Pop().GetBigInteger()
                x = estack.Pop().GetBigInteger()

                estack.PushT(x << n)

            elif opcode == SHR:

                n = estack.Pop().GetBigInteger()
                x = estack.Pop().GetBigInteger()

                estack.PushT(x >> n)

            elif opcode == BOOLAND:

                x2 = estack.Pop().GetBoolean()
                x1 = estack.Pop().GetBoolean()

                estack.PushT(x1 and x2)

            elif opcode == BOOLOR:

                x2 = estack.Pop().GetBoolean()
                x1 = estack.Pop().GetBoolean()

                estack.PushT(x1 or x2)

            elif opcode == NUMEQUAL:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(x2 == x1)

            elif opcode == NUMNOTEQUAL:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(x1 != x2)

            elif opcode == LT:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(x1 < x2)

            elif opcode == GT:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(x1 > x2)

            elif opcode == LTE:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(x1 <= x2)

            elif opcode == GTE:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(x1 >= x2)

            elif opcode == MIN:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()
                estack.PushT(min(x1, x2))

            elif opcode == MAX:

                x2 = estack.Pop().GetBigInteger()
                x1 = estack.Pop().GetBigInteger()

                estack.PushT(max(x1, x2))

            elif opcode == WITHIN:

                b = estack.Pop().GetBigInteger()
                a = estack.Pop().GetBigInteger()
                x = estack.Pop().GetBigInteger()

                estack.PushT(a <= x and x < b)

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

                try:

                    res = self.Crypto.VerifySignature(self.ScriptContainer.GetMessage(), sig, pubkey)
                    estack.PushT(res)

                except Exception as e:
                    estack.PushT(False)
                    logger.error("Could not checksig: %s " % e)
                return

            elif opcode == CHECKMULTISIG:

                n = estack.Pop().GetBigInteger()

                if n < 1:
                    return self.VM_FAULT_and_report(VMFault.CHECKMULTISIG_INVALID_PUBLICKEY_COUNT)

                pubkeys = []
                for i in range(0, n):
                    pubkeys.append(estack.Pop().GetByteArray())

                m = estack.Pop().GetBigInteger()

                if m < 1 or m > n:
                    return self.VM_FAULT_and_report(VMFault.CHECKMULTISIG_SIGNATURE_ERROR, m, n)

                sigs = []

                for i in range(0, m):
                    sigs.append(estack.Pop().GetByteArray())

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

                if not item.IsArray:
                    estack.PushT(len(item.GetByteArray()))

                else:
                    estack.PushT(len(item.GetArray()))

            elif opcode == PACK:

                size = estack.Pop().GetBigInteger()

                if size < 0 or size > estack.Count:
                    return self.VM_FAULT_and_report(VMFault.UNKNOWN8)

                items = []

                for i in range(0, size):
                    topack = estack.Pop()
                    items.append(topack)

                estack.PushT(items)

            elif opcode == UNPACK:
                item = estack.Pop()

                if not item.IsArray:
                    return self.VM_FAULT_and_report(VMFault.UNPACK_INVALID_TYPE, item)

                items = item.GetArray()
                items.reverse()

                [estack.PushT(i) for i in items]

                estack.PushT(len(items))

            elif opcode == PICKITEM:

                index = estack.Pop().GetBigInteger()
                if index < 0:
                    return self.VM_FAULT_and_report(VMFault.PICKITEM_NEGATIVE_INDEX)

                item = estack.Pop()

                if not item.IsArray:
                    return self.VM_FAULT_and_report(VMFault.PICKITEM_INVALID_TYPE, index, item)

                items = item.GetArray()

                if index >= len(items):
                    return self.VM_FAULT_and_report(VMFault.PICKITEM_INVALID_INDEX, index, len(items))

                to_pick = items[index]

                estack.PushT(to_pick)

            elif opcode == SETITEM:
                newItem = estack.Pop()

                if issubclass(type(newItem), StackItem) and newItem.IsStruct:
                    newItem = newItem.Clone()

                index = estack.Pop().GetBigInteger()

                arrItem = estack.Pop()

                if not issubclass(type(arrItem), StackItem) or not arrItem.IsArray:
                    return self.VM_FAULT_and_report(VMFault.SETITEM_INVALID_TYPE)

                items = arrItem.GetArray()

                if index < 0 or index >= len(items):
                    return self.VM_FAULT_and_report(VMFault.SETITEM_INVALID_INDEX)

                items[index] = newItem

            elif opcode == NEWARRAY:

                count = estack.Pop().GetBigInteger()
                items = [None for i in range(0, count)]
                estack.PushT(Array(items))

            elif opcode == NEWSTRUCT:

                count = estack.Pop().GetBigInteger()

                items = [None for i in range(0, count)]

                estack.PushT(Struct(items))

            elif opcode == APPEND:
                newItem = estack.Pop()

                if type(newItem) is Struct:
                    newItem = newItem.Clone()

                arrItem = estack.Pop()

                if not arrItem.IsArray:
                    return self.VM_FAULT_and_report(VMFault.APPEND_INVALID_TYPE, arrItem)

                arr = arrItem.GetArray()
                arr.append(newItem)

            elif opcode == REVERSE:

                arrItem = estack.Pop()
                if not arrItem.IsArray:
                    return self.VM_FAULT_and_report(VMFault.REVERSE_INVALID_TYPE, arrItem)

                arrItem.GetArray().reverse()

            elif opcode == REMOVE:
                index = estack.Pop().GetBigInteger()
                arrItem = estack.Pop()
                if not arrItem.IsArray:
                    return self.VM_FAULT_and_report(VMFault.REMOVE_INVALID_TYPE, arrItem, index)
                items = arrItem.GetArray()

                if index < 0 or index >= len(items):
                    return self.VM_FAULT_and_report(VMFault.REMOVE_INVALID_INDEX, index, len(items))

                del items[index]

            elif opcode == THROW:
                return self.VM_FAULT_and_report(VMFault.THROW)

            elif opcode == THROWIFNOT:
                if not estack.Pop().GetBoolean():
                    return self.VM_FAULT_and_report(VMFault.THROWIFNOT)

            elif opcode == DEBUG:
                pdb.set_trace()
                return

            else:
                return self.VM_FAULT_and_report(VMFault.UNKNOWN_OPCODE, opcode)

        if self._VMState & VMState.FAULT == 0 and self.InvocationStack.Count > 0:

            if self.CurrentContext.InstructionPointer in self.CurrentContext.Breakpoints:
                self._VMState |= VMState.BREAK

    def LoadScript(self, script, push_only=False):

        context = ExecutionContext(self, script, push_only)
        self._InvocationStack.PushT(context)

        self._ExecutedScriptHashes.append(context.ScriptHash())

    def RemoveBreakPoint(self, position):

        if self._InvocationStack.Count == 0:
            return False
        return self.CurrentContext.Breakpoints.remove(position)

    def StepInto(self):
        if self._InvocationStack.Count == 0:
            logger.info("INVOCATION COUNT IS 0, HALT")
            self._VMState |= VMState.HALT

        if self._VMState & VMState.HALT > 0 or self._VMState & VMState.FAULT > 0:
            logger.info("stopping because vm state is %s " % self._VMState)
            return

        op = None

        if self.CurrentContext.InstructionPointer >= len(self.CurrentContext.Script):
            op = RET
        else:
            op = self.CurrentContext.OpReader.ReadByte(do_ord=False)

        #        opname = ToName(op)
        #        logger.info("____________________________________________________")
        #        logger.info("[%s] [%s] %02x -> %s" % (self.CurrentContext.InstructionPointer,self.ops_processed,int.from_bytes(op,byteorder='little'), opname))
        #        logger.info("-----------------------------------")

        self.ops_processed += 1

        try:
            self.write_log("{} {}".format(self.ops_processed, ToName(op)))
            self.ExecuteOp(op, self.CurrentContext)
        except Exception as e:
            error_msg = "COULD NOT EXECUTE OP (%s): %s %s %s" % (self.ops_processed, e, op, ToName(op))
            self.write_log(error_msg)

            if self._exit_on_error:
                self._VMState |= VMState.FAULT
            else:
                logger.error(error_msg)
                logger.exception(e)

    def StepOut(self):
        self._VMState &= ~VMState.BREAK
        count = self._InvocationStack.Count

        while self._VMState & VMState.HALT == 0 and \
                self._VMState & VMState.FAULT == 0 and \
                self._VMState & VMState.BREAK == 0 and \
                self._InvocationStack.Count > count:
            self.StepInto()

    def StepOver(self):
        if self._VMState & VMState.HALT > 0 or self._VMState & VMState.FAULT > 0:
            return

        self._VMState &= ~VMState.BREAK
        count = self._InvocationStack.Count

        while self._VMState & VMState.HALT == 0 and \
                self._VMState & VMState.FAULT == 0 and \
                self._VMState & VMState.BREAK == 0 and \
                self._InvocationStack.Count > count:
            self.StepInto()

    def VM_FAULT_and_report(self, id, *args):
        self._VMState |= VMState.FAULT

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
            error_msg = "Cannot access item at index {}. Item is not an array but of type: {}".format(index, type(item))

        elif id == VMFault.PICKITEM_NEGATIVE_INDEX:
            error_msg = "Attempting to access an array using a negative index"

        elif id == VMFault.PICKITEM_INVALID_INDEX:
            index = args[0]
            length = args[1]
            error_msg = "Array index {} exceeds list length {}".format(index, length)

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

        elif id == VMFault.UNKNOWN_OPCODE:
            opcode = args[0]
            error_msg = "Unknown opcode found: {}".format(opcode)

        else:
            error_msg = id
            pass

        logger.error("({}) {}".format(self.ops_processed, error_msg))
        return
