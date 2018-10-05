from neo.IO.MemoryStream import StreamManager
from neocore.IO.BinaryReader import BinaryReader
from neo.VM.RandomAccessStack import RandomAccessStack


class ExecutionContext:
    Script = None

    __OpReader = None

    __mstream = None

    _RVCount = None

    _EvaluationStack = None
    _AltStack = None

    @property
    def EvaluationStack(self):
        return self._EvaluationStack

    @property
    def AltStack(self):
        return self._AltStack

    @property
    def OpReader(self):
        return self.__OpReader

    @property
    def InstructionPointer(self):
        return self.__OpReader.stream.tell()

    @InstructionPointer.setter
    def InstructionPointer(self, value):
        self.__OpReader.stream.seek(value)

    def SetInstructionPointer(self, value):
        self.__OpReader.stream.seek(value)

    @property
    def NextInstruction(self):
        return self.Script[self.__OpReader.stream.tell()].to_bytes(1, 'little')

    _script_hash = None

    def ScriptHash(self):
        if self._script_hash is None:
            self._script_hash = self.crypto.Hash160(self.Script)
        return self._script_hash

    def __init__(self, engine=None, script=None, rvcount=0):
        self.Script = script
        self.__mstream = StreamManager.GetStream(self.Script)
        self.__OpReader = BinaryReader(self.__mstream)
        self._EvaluationStack = RandomAccessStack(name='Evaluation')
        self._AltStack = RandomAccessStack(name='Alt')
        self._RVCount = rvcount
        self.crypto = engine.Crypto

    def Dispose(self):
        self.__OpReader = None
        StreamManager.ReleaseStream(self.__mstream)
