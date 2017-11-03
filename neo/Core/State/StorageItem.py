
from .StateBase import StateBase
import sys
from neo.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream, StreamManager


class StorageItem(StateBase):

    Value = None

    def __init__(self, value=None):
        if value is None:
            self.Value = bytearray(0)
        else:
            self.Value = value

    def Clone(self):
        return StorageItem(value=self.Value)

    def FromReplica(self, replica):
        self.Value = replica.Value

    def Size(self):
        return super(StorageItem, self).Size() + len(self.Value)

    def Deserialize(self, reader):
        super(StorageItem, self).Deserialize(reader)
        self.Value = reader.ReadVarBytes()

    @staticmethod
    def DeserializeFromDB(buffer):
        m = StreamManager.GetStream(buffer)
        reader = BinaryReader(m)
        v = StorageItem()
        v.Deserialize(reader)
        StreamManager.ReleaseStream(m)
        return v

    def Serialize(self, writer):
        super(StorageItem, self).Serialize(writer)
        writer.WriteVarBytes(self.Value)
