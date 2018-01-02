from neocore.IO.Mixins import SerializableMixin
import mmh3
from neocore.BigInteger import BigInteger


class StorageKey(SerializableMixin):
    ScriptHash = None
    Key = None

    def __init__(self, script_hash=None, key=None):
        """
        Create an instance.

        Args:
            script_hash (UInt160):
            key (bytes):
        """
        self.ScriptHash = script_hash
        self.Key = key

    def _murmur(self):
        """
        Get the murmur hash of the key.

        Returns:
            int: 32-bit
        """
        return mmh3.hash(bytes(self.Key))

    def GetHashCode(self):
        """
        Get the hash code of the key.

        Returns:
            int:
        """
        return abs(self.ScriptHash.GetHashCode() + self._murmur())

    def GetHashCodeBytes(self):
        """
        Get the hash code in bytes.

        Returns:
            bytes:
        """
        bigint = BigInteger(self.GetHashCode())
        return bigint.ToByteArray()

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neocore.IO.BinaryReader):
        """
        self.ScriptHash = reader.ReadUInt160()
        self.Key = reader.ReadBytes()

    def Serialize(self, writer):
        """
        Serialize full object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        writer.WriteUInt160(self.ScriptHash)
        writer.WriteVarBytes(self.Key)

    def __eq__(self, other):
        if other is None:
            return False
        if other is self:
            return True

        return self.ScriptHash == other.ScriptHash and self.Key == other.Key
