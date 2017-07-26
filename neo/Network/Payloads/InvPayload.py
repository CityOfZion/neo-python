
from neo.IO.Mixins import SerializableMixin
import sys

class InvPayload(SerializableMixin):

    InventoryType = None
    Hashes = []

    def __init__(self, type, hashes):
        self.InventoryType = type
        self.Hashes = hashes if hashes else []


    def DistinctHashes(self):
        return list(set(self.Hashes))

    def Size(self):
        return sys.getsizeof(self.InventoryType) + sys.getsizeof(self.Hashes)


    def Deserialize(self, reader):

        self.InventoryType = reader.ReadByte()

        self.Hashes = reader.ReadSerializableArray()


    def Serialize(self, writer):
        writer.WriteByte(self.InventoryType)
        writer.WriteSerializeableArray(self.Hashes)

