import hashlib
import sys
import os
import traceback
import pdb

from logzero import logger

from neo.VM.RandomAccessStack import RandomAccessStack
from neo.VM.ExecutionContext import ExecutionContext
from neo.VM import VMState
from neo.VM.OpCode import *
from neo.SmartContract.ContractParameterType import ContractParameterType
from neocore.BigInteger import BigInteger
from neo.VM.InteropService import Array, Struct, StackItem
from neocore.UInt160 import UInt160


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
    def EntryContext(self):
        return self.InvocationStack.Peek(self.InvocationStack.Count - 1)

    @property
    def ExecutedScriptHashes(self):
        return self._ExecutedScriptHashes

    def __init__(self, container=None, crypto=None, table=None, service=None):
        self._ScriptContainer = container
        self._Crypto = crypto
        self._Table = table
        self._Service = service

        self._InvocationStack = RandomAccessStack(name='Invocation')
        self._EvaluationStack = RandomAccessStack(name='Evaluation')
        self._AltStack = RandomAccessStack(name='Alt')
        self._ExecutedScriptHashes = []
        self.ops_processed = 0

    def AddBreakPoint(self, position):
        self.CurrentContext.Breakpoints.add(position)

    def ResultsForCode(self, contract):
        try:
            return_type = ContractParameterType(contract.ReturnType)

            item = self.EvaluationStack.Items[0]
            if return_type == ContractParameterType.Integer:
                return item.GetBigInteger()
            elif return_type == ContractParameterType.Boolean:
                return item.GetBoolean()
            elif return_type == ContractParameterType.ByteArray:
                return item.GetByteArray()
            elif return_type == ContractParameterType.String:
                return item.GetString()
            elif return_type == ContractParameterType.Array:
                return item.GetArray()
            else:
                logger.error("Could not format results for return type %s " % return_type)
            return item
        except Exception as e:
            pass

        return self.EvaluationStack.Items

    def Dispose(self):
        while self._InvocationStack.Count > 0:
            self._InvocationStack.Pop().Dispose()

    def Execute(self):
        self._VMState &= ~VMState.BREAK

        while self._VMState & VMState.HALT == 0 and self._VMState & VMState.FAULT == 0 and self._VMState & VMState.BREAK == 0:
            self.StepInto()

    def ExecuteOp(self, opcode, context):
        estack = self._EvaluationStack
        istack = self._InvocationStack
        astack = self._AltStack

        if opcode > PUSH16 and opcode != RET and context.PushOnly:
            self._VMState |= VMState.FAULT

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
                    self._VMState |= VMState.FAULT
                    return

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
                    self._VMState |= VMState.FAULT
                    return

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
                    self._VMState |= VMState.FAULT
                    return

                if opcode == TAILCALL:
                    istack.Pop().Dispose()

                self.LoadScript(script)

            elif opcode == SYSCALL:
                call = context.OpReader.ReadVarBytes(252).decode('ascii')
                if not self._Service.Invoke(call, self):
                    self._VMState |= VMState.FAULT

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
                    self._VMState |= VMState.FAULT
                    return

                # if n == 0 break, same as do x if n > 0
                if n > 0:

                    item = estack.Peek(n)
                    estack.Set(n, estack.Peek())
                    estack.Set(0, item)

            elif opcode == XTUCK:
                n = estack.Pop().GetBigInteger()

                if n <= 0:
                    self._VMState |= VMState.FAULT
                    return

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
                    self._VMState |= VMState.FAULT
                    return

                estack.PushT(estack.Peek(n))

            elif opcode == ROLL:

                n = estack.Pop().GetBigInteger()
                if n < 0:
                    self._VMState |= VMState.FAULT
                    return

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
                    self._VMState |= VMState.FAULT
                    return

                index = estack.Pop().GetBigInteger()
                if index < 0:
                    self._VMState |= VMState.FAULT
                    return

                x = estack.Pop().GetByteArray()

                estack.PushT(x[index:count + index])

            elif opcode == LEFT:

                count = estack.Pop().GetBigInteger()
                if count < 0:
                    self._VMState |= VMState.FAULT
                    return

                x = estack.Pop().GetByteArray()
                estack.PushT(x[:count])

            elif opcode == RIGHT:

                count = estack.Pop().GetBigInteger()
                if count < 0:
                    self._VMState |= VMState.FAULT
                    return

                x = estack.Pop().GetByteArray()
                if len(x) < count:
                    self._VMState |= VMState.FAULT
                    return

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

            elif opcode == CHECKMULTISIG:

                n = estack.Pop().GetBigInteger()

                if n < 1:
                    self._VMState |= VMState.FAULT
                    return

                pubkeys = []
                for i in range(0, n):
                    pubkeys.append(estack.Pop().GetByteArray())

                m = estack.Pop().GetBigInteger()

                if m < 1 or m > n:
                    self._VMState |= VMState.FAULT
                    return

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
                    self._VMState |= VMState.FAULT
                    return

                if not item.IsArray:
                    estack.PushT(len(item.GetByteArray()))

                else:
                    estack.PushT(len(item.GetArray()))

            elif opcode == PACK:

                size = estack.Pop().GetBigInteger()

                if size < 0 or size > estack.Count:
                    self._VMState |= VMState.FAULT
                    return

                items = []

                for i in range(0, size):
                    topack = estack.Pop()
                    items.append(topack)

                estack.PushT(items)

            elif opcode == UNPACK:
                item = estack.Pop()

                if not item.IsArray:
                    self._VMState |= VMState.FAULT
                    return

                items = item.GetArray()
                items.reverse()

                [estack.PushT(i) for i in items]

                estack.PushT(len(items))

            elif opcode == PICKITEM:

                index = estack.Pop().GetBigInteger()

                if index < 0:
                    self._VMState |= VMState.FAULT
                    return

                item = estack.Pop()

                if not item.IsArray:
                    self._VMState |= VMState.FAULT
                    return

                items = item.GetArray()

                if index >= len(items):
                    self._VMState |= VMState.FAULT
                    return

                to_pick = items[index]
                estack.PushT(to_pick)

            elif opcode == SETITEM:
                newItem = estack.Pop()

                if issubclass(type(newItem), StackItem) and newItem.IsStruct:
                    newItem = newItem.Clone()

                index = estack.Pop().GetBigInteger()

                arrItem = estack.Pop()

                if not issubclass(type(arrItem), StackItem) or not arrItem.IsArray:
                    self._VMState |= VMState.FAULT
                    return

                items = arrItem.GetArray()

                if index < 0 or index >= len(items):
                    self._VMState |= VMState.FAULT
                    return

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
                    self._VMState |= VMState.FAULT
                    return

                arr = arrItem.GetArray()
                arr.append(newItem)

            elif opcode == REVERSE:

                arrItem = estack.Pop()
                if not arrItem.IsArray:
                    self._VMState |= VMState.FAULT
                    return
                arrItem.GetArray().reverse()

            elif opcode == REMOVE:
                index = estack.Pop().GetBigInteger()
                arrItem = estack.Pop()
                if not arrItem.IsArray:
                    self._VMState |= VMState.FAULT
                    return
                items = arrItem.GetArray()

                if index < 0 or index >= len(items):
                    self._VMState |= VMState.FAULT
                    return
                del items[index]

            elif opcode == THROW:
                self._VMState |= VMState.FAULT
                return

            elif opcode == THROWIFNOT:
                if not estack.Pop().GetBoolean():
                    self._VMState |= VMState.FAULT
                    return

            elif opcode == DEBUG:
                pdb.set_trace()
                return

            else:

                self._VMState |= VMState.FAULT
                return

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
#        logger.info("[%s] %02x -> %s" % (self.ops_processed,int.from_bytes(op,byteorder='little'), opname))
#        logger.info("-----------------------------------")

        self.ops_processed += 1

        try:
            self.ExecuteOp(op, self.CurrentContext)
        except Exception as e:
            logger.error("COULD NOT EXECUTE OP: %s %s %s" % (e, op, ToName(op)))
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
