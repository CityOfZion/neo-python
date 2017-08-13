
from neo.VM.RandomAccessStack import RandomAccessStack
from neo.VM.ExecutionContext import ExecutionContext
from neo.VM import VMState
from neo.VM.OpCode import *

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
        self._VMState &= VMState.BREAK

#        while (!State.HasFlag(VMState.HALT) & & !State.HasFlag(VMState.FAULT) & & !State.HasFlag(VMState.BREAK))
#        StepInto();

        while self._VMState & VMState.HALT == 0 and self._VMState & VMState.FAULT == 0 and self._VMState & VMState.BREAK == 0:
            self.StepInto()


    def ExecuteOp(self, opcode, context):
        pass

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

        if self._VMState & VMState.HALT or self._VMState & VMState.FAULT:
            print("stopping because vm state is %s " % self._VMState)

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

            self._VMState |= VMState.FAULT



    def StepOut(self):
        pass

    def StepOver(self):
        pass