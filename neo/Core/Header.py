# -*- coding: UTF-8 -*-

from neo.Core.BlockBase import BlockBase
from neo.IO.MemoryStream import MemoryStream
from neo.IO.BinaryReader import BinaryReader
from bitarray import bitarray

class Header(BlockBase):

    def Size(self):
        return super(Header,self).Size() + 1

    def Deserialize(self, reader):
        super(Header, self).Deserialize(reader)
        if reader.ReadByte() != 0:
            raise Exception('Incorrect Header Format')

    def Equals(self, other):

        if other is None: return False
        if other is self: return True
        return self.Hash() == other.Hash()

    @staticmethod
    def FromTrimmedData(data, index):

        header = Header()

        ms = MemoryStream()

        reader = BinaryReader(ms)

        header.DeserializeUnsigned(reader)
        reader.ReadByte()
        header.Script = reader.ReadSerializableArray()

        return header

    def GetHashCode(self):
        return self.Hash()


    def Serialize(self, writer):

        super(Header, self).Serialize(writer)
        writer.WriteByte(0x00)

