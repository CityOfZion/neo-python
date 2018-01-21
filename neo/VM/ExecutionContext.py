from neo.IO.MemoryStream import MemoryStream, StreamManager
from neocore.IO.BinaryReader import BinaryReader


class ExecutionContext():

    _Engine = None

    Script = None

    PushOnly = False

    __OpReader = None

    __mstream = None

    __Breakpoints = None

    @property
    def OpReader(self):
        return self.__OpReader

    @property
    def Breakpoints(self):
        return self.__Breakpoints

    @property
    def InstructionPointer(self):
        return self.__OpReader.stream.tell()

    def SetInstructionPointer(self, value):
        self.__OpReader.stream.seek(value)

    @property
    def NextInstruction(self):
        return self.Script[self.__OpReader.stream.tell()].to_bytes(1, 'little')

    _script_hash = None

    def ScriptHash(self):
        if self._script_hash is None:
            self._script_hash = self._Engine.Crypto.Hash160(self.Script)
        return self._script_hash

    def __init__(self, engine=None, script=None, push_only=False, break_points=set()):
        self._Engine = engine
        self.Script = script
        self.PushOnly = push_only
        self.__Breakpoints = break_points
        self.__mstream = StreamManager.GetStream(self.Script)
        self.__OpReader = BinaryReader(self.__mstream)

    def Clone(self):

        context = ExecutionContext(self._Engine, self.Script, self.PushOnly, self.__Breakpoints)
        context.SetInstructionPointer(self.InstructionPointer)

        return context

    def Dispose(self):
        self.__OpReader = None
        StreamManager.ReleaseStream(self.__mstream)
