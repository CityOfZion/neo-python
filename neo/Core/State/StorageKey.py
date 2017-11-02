
from neo.IO.Mixins import SerializableMixin
import mmh3
from neo.BigInteger import BigInteger


class StorageKey(SerializableMixin):

    ScriptHash = None
    Key = None

    def __init__(self, script_hash=None, key=None):
        self.ScriptHash = script_hash
        self.Key = key

    def _murmur(self):
        return mmh3.hash(bytes(self.Key))

    def GetHashCode(self):
        return abs(self.ScriptHash.GetHashCode() + self._murmur())

    def GetHashCodeBytes(self):
        bigint = BigInteger(self.GetHashCode())
        return bigint.ToByteArray()

    def Deserialize(self, reader):
        self.ScriptHash = reader.ReadUInt160()
        self.Key = reader.ReadBytes()

    def Serialize(self, writer):
        writer.WriteUInt160(self.ScriptHash)
        writer.WriteVarBytes(self.Key)

    def __eq__(self, other):
        if other is None:
            return False
        if other is self:
            return True

        return self.ScriptHash == other.ScriptHash and self.Key == other.Key
