
from neo.IO.Mixins import SerializableMixin
import sys
from autologging import logged

@logged
class InvPayload(SerializableMixin):

    Type = None
    Hashes = []

    def __init__(self, type=None, hashes=None):
        self.Type = type
        self.Hashes = hashes if hashes else []

#    @property
#    def DistinctHashes(self):
##        return [h.ToBytes() for h in self.Hashes]
#        return set(self.Hashes)

    def Size(self):
        return sys.getsizeof(self.Type) + sys.getsizeof(self.Hashes)


    def Deserialize(self, reader):

        self.Type = reader.ReadByte()

        self.Hashes = reader.ReadHashes()


    def Serialize(self, writer):
        try:
            writer.WriteByte(self.Type)
#            print("WILL WRITE HASHES %s " % self.Hashes)
            writer.WriteHashes(self.Hashes)
        except Exception as e:
            self.__log.debug("COULD NOT WRITE INVENTORY HASHES %s " % e)

    def ToString(self):
        return "INVENTORY Type %s hashes %s " % (self.Type,[h for h in self.Hashes])