
from neo.IO.Mixins import SerializableMixin
import ctypes


class StateBase(SerializableMixin):

    StateVersion= 0


    def Size(self):
        return ctypes.sizeof(ctypes.c_byte)



    def Deserialize(self, reader):
        if reader.ReadByte() != self.StateVersion:
            raise Exception("Incorrect State format")

    def Serialize(self, writer):
        writer.WriteByte(self.StateVersion)