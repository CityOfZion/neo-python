from neo.IO.MemoryStream import StreamManager
from neo.Core.IO.BinaryReader import BinaryReader
from neo.VM.RandomAccessStack import RandomAccessStack
from neo.VM.OpCode import RET
from neo.VM.Instruction import Instruction
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from neo.VM.Script import Script


class ExecutionContext:

    def __init__(self, script: 'Script', callingScriptHash: bytearray, rvcount: int):
        self.instructions = {}
        self._EvaluationStack = RandomAccessStack(name='Evaluation')
        self._AltStack = RandomAccessStack(name='Alt')
        self.InstructionPointer = 0
        self.Script = script
        self._RVCount = rvcount
        self._script_hash = None
        self.CallingScriptHash = callingScriptHash

    @property
    def EvaluationStack(self):
        return self._EvaluationStack

    @property
    def AltStack(self):
        return self._AltStack

    @property
    def CurrentInstruction(self):
        return self.GetInstruction(self.InstructionPointer)

    @property
    def NextInstruction(self):
        return self.GetInstruction(self.InstructionPointer + self.CurrentInstruction.Size)

    def ScriptHash(self):
        return self.Script.ScriptHash

    def GetInstruction(self, ip) -> Instruction:
        if ip >= self.Script.Length:
            return Instruction.RET()
        instruction = self.instructions.get(ip, None)

        if instruction is None:
            instruction = Instruction.FromScriptAndIP(self.Script, ip)
            self.instructions.update({ip: instruction})

        return instruction

    def MoveNext(self):
        self.InstructionPointer += self.CurrentInstruction.Size
        return self.InstructionPointer < self.Script.Length

    def Dispose(self):
        self.__OpReader = None
        StreamManager.ReleaseStream(self.__mstream)
