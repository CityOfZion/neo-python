
from neo.IO.Mixins import SerializableMixin
import sys
import ctypes


class FilterLoadPayload(SerializableMixin):

    Filter = None
    K = None
    Tweak = None

    def __init__(self, filter=None):

        if filter:
            ba = bytearray(int(filter.M / 8))
            filter.GetBits(ba)

            self.Filter = ba
            self.K = filter.K
            self.Tweak = filter.Tweak

    def Size(self):
        return sys.getsizeof(self.Filter) + ctypes.sizeof(ctypes.c_byte) + ctypes.sizeof(ctypes.c_uint)

    def Deserialize(self, reader):
        self.Filter = reader.ReadVarBytes(36000)
        self.K = reader.ReadByte()
        if self.K > 50:
            raise Exception('Invalid format')
        self.Tweak = reader.ReadUInt32()

    def Serialize(self, writer):
        writer.WriteVarBytes(self.Filter)
        writer.Write(self.K)
        writer.Write(self.Tweak)
