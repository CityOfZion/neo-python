
from neo.IO.Mixins import SerializableMixin
import sys
from autologging import logged


@logged
class GetBlocksPayload(SerializableMixin):

    HashStart = []
    HashStop = None

    def __init__(self, hash_start=None, hash_stop=None):

        self.HashStart = [] if not hash_start else [hash_start,]
        self.HashStop = hash_stop


    def Size(self):
        return sys.getsizeof(self.HashStart) + sys.getsizeof(self.HashStop)


    def Deserialize(self, reader):
        self.HashStart = reader.ReadHashes()
        self.HashStop = reader.ReadUInt256()


    def Serialize(self, writer):
        self.__log.debug("Writing hash start... %s " % self.HashStart)
        writer.WriteHashes(self.HashStart)
        if self.HashStop is not None:
            writer.WriteUInt256(self.HashStop)
        else:
            writer.WriteUInt256( bytearray(32))

