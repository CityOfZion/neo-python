
from neo.VM.RandomAccessStack import RandomAccessStack
from neo.VM.ExecutionContext import ExecutionContext
from neo.VM import VMState
from neo.VM.OpCode import *
from autologging import logged

@logged
class ExecutionEngine():

    _Table=None
    _Service = None

    _ScriptContainer = None
    _Crypto = None

    _VMState = VMState.BREAK


    _InvocationStack=None
    _EvaluationStack=None
    _AltStack = None



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
        return self.InvocationStack.Peek( self.InvocationStack.Count - 1)

    def ExecutionEngine(self, container, crypto, table=None, service = None):
        self._ScriptContainer = container
        self._Crypto = crypto
        self._Table = table
        self._Service = service

        self._InvocationStack = RandomAccessStack()
        self._EvaluationStack = RandomAccessStack()
        self._AltStack = RandomAccessStack()



    def AddBreakPoint(self, position):
        self.CurrentContext.Breakpoints.add(position)


    def Dispose(self):
        while self._InvocationStack.Count > 0:
            self._InvocationStack.Pop().Dispose()


    def Execute(self):
        self._VMState &= ~VMState.BREAK

#        while (!State.HasFlag(VMState.HALT) & & !State.HasFlag(VMState.FAULT) & & !State.HasFlag(VMState.BREAK))
#        StepInto();

        while self._VMState & VMState.HALT == 0 and self._VMState & VMState.FAULT == 0 and self._VMState & VMState.BREAK == 0:
            self.StepInto()


    def ExecuteOp(self, opcode, context):
        estack = self._EvaluationStack
        istack = self._InvocationStack
        astack = self._AltStack

        if opcode > PUSH16 and opcode != RET and context.PushOnly:
            self._VMState |= VMState.FAULT

        if opcode >= PUSHBYTES1 and opcode <= PUSHBYTES75:
            estack.PushT(context.OpReader.ReadBytes(opcode))
        else:

            # push values
            pushops = [PUSHM1,PUSH1,PUSH2,PUSH3,PUSH4,PUSH5,PUSH6,PUSH7,PUSH8,
                       PUSH9,PUSH10,PUSH11,PUSH12,PUSH13,PUSH14,PUSH15,PUSH16 ]

            if opcode == PUSH0:
                estack.PushT(bytearray(0))

            elif opcode == PUSHDATA1:
                estack.PushT(context.OpReader.ReadByte())
            elif opcode == PUSHDATA2:
                estack.PushT(context.OpReader.ReadUInt16())
            elif opcode == PUSHDATA4:
                estack.PushT(context.OpReader.ReadUInt32())
            elif opcode in pushops:
                # EvaluationStack.Push((int)opcode - (int)OpCode.PUSH1 + 1);
                estack.PushT(opcode - PUSH1 + 1)

            #control
            elif opcode == NOP:
                pass
            elif opcode in [JMP, JMPIF, JMPIFNOT]:
                offset = context.OpReader.ReadInt16()
                offset = context.GetInstructionPointer + offset - 3
                if offset < 0 or offset > context.Script.Length:
                    self._VMSTATE |= VMState.FAULT
                    return

                fValue = True
                if opcode > JMP:
                    fValue = estack.Pop().GetBoolean()
                    if opcode == JMPIFNOT:
                        fValue = not fValue
                if fValue:
                    context.InstructionPointer = offset


            elif opcode == CALL:
                istack.PushT(context.Clone())
                context.SetInstructionPointer( context.GetInstructionPointer() + 2)
                self.ExecuteOp(JMP, self.CurrentContext)

            elif opcode == RET:
                istack.Pop().Dispose()
                if istack.Count == 0:
                    self._VMState |= VMState.HALT

            elif opcode == APPCALL or opcode == TAILCALL:

                if self._Table == None:
                    self._VMState |= VMState.FAULT
                    return

                script_hash = context.OpReader.ReadBytes(20)
                script = self._Table.GetScript(script_hash)

                if script == None:
                    self._VMState |= VMState.FAULT
                    return

                if opcode == TAILCALL:
                    istack.Pop().Dispose()

                self.LoadScript(script)

            elif opcode == SYSCALL:

                if not self._Service.Invoke( context.OpReader.ReadVarBytes(252).decode('ascii'), self):
                    self._VMState |= VMState.FAULT

            #stack operations
            elif opcode == DUPFROMALTSTACK:
                estack.PushT(astack.Peek())

            elif opcode == TOALTSTACK:
                astack.PushT(estack.Pop())

            elif opcode == FROMALTSTACK:
                estack.PushT(astack.Pop())



    def LoadScript(self, script, push_only=False):

        context = ExecutionContext(self, script, push_only)
        self._InvocationStack.PushT(context)

    def RemoveBreakPoint(self, position):

        if self._InvocationStack.Count == 0:
            return False
        return self.CurrentContext.Breakpoints.remove(position)

    def StepInto(self):
        if self._InvocationStack.Count == 0:
            self._VMState |= VMState.HALT

        if self._VMState & VMState.HALT > 0 or self._VMState & VMState.FAULT > 0:
            self.__log.debug("stopping because vm state is %s " % self._VMState)

        op = None
        if self.CurrentContext.GetInstructionPointer() >= len(self.CurrentContext.Script):
            op = RET
        else:
            op = self.CurrentContext.OpReader.ReadByte()
        print("op is %s " % op)


        try:
            self.ExecuteOp(op, self.CurrentContext)
        except Exception as e:
            print("exception: %s " % e)
            self.__log.error("Exception executing op %s " % e)

            self._VMState |= VMState.FAULT



    def StepOut(self):
        self._VMState &= ~VMState.BREAK
        count = self._InvocationStack.Count

        while   self._VMState & VMState.HALT == 0 and \
                self._VMState & VMState.FAULT == 0 and \
                self._VMState & VMState.BREAK == 0 and \
                self._InvocationStack.Count > count:

            self.StepInto()

    def StepOver(self):
        if self._VMState & VMState.HALT > 0 or self._VMState & VMState.FAULT > 0: return

        self._VMState &= ~VMState.BREAK
        count = self._InvocationStack.Count

        while   self._VMState & VMState.HALT == 0 and \
                self._VMState & VMState.FAULT == 0 and \
                self._VMState & VMState.BREAK == 0 and \
                self._InvocationStack.Count > count:

            self.StepInto()
