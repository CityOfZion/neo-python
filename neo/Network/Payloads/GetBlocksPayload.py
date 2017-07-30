
from neo.IO.Mixins import SerializableMixin
import sys

class GetBlocksPayload(SerializableMixin):

    HashStart = []
    HashStop = None

    def __init__(self, hash_start=None, hash_stop=None):

        self.HashStart = [] if not hash_start else [hash_start,]
        self.HashStop = hash_stop


    def Size(self):
        return sys.getsizeof(self.HashStart) + sys.getsizeof(self.HashStop)


    def Deserialize(self, reader):
        self.HashStart = reader.ReadSerializeableArray(16)
        self.HashStop = reader.ReadSerializeable()


    def Serialize(self, writer):
        writer.WriteHashes(self.HashStart)
        if self.HashStop is not None:
            writer.WriteUInt256(self.HashStop)
        

