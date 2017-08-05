
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


    def DistinctHashes(self):
        hh = []
        for h in self.Hashes:
            if not h in hh:
                hh.append(h)
        return hh

    def Size(self):
        return sys.getsizeof(self.Type) + sys.getsizeof(self.Hashes)


    def Deserialize(self, reader):

        self.Type = reader.ReadByte()

        self.Hashes = reader.ReadHashes()


    def Serialize(self, writer):
        try:
            writer.WriteByte(self.Type)
            writer.WriteHashes(self.Hashes)
        except Exception as e:
            print("COULD NOT WRITE INVENTORY HASHES %s " % e)
