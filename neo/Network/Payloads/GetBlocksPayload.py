import sys
import binascii
from neocore.IO.Mixins import SerializableMixin
from neocore.UInt256 import UInt256
from neo.Core.Size import GetVarSize


class GetBlocksPayload(SerializableMixin):
    HashStart = []
    HashStop = None

    def __init__(self, hash_start=[], hash_stop=UInt256()):
        """
        Create an instance.

        Args:
            hash_start (list): a list of hash values. Each value is of the bytearray type. Note: should actually be UInt256 objects.
            hash_stop (UInt256):
        """
        self.HashStart = hash_start
        self.HashStop = hash_stop

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        corrected_hashes = list(map(lambda i: UInt256(data=binascii.unhexlify(i)), self.HashStart))
        return GetVarSize(corrected_hashes) + self.hash_stop.Size

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neo.IO.BinaryReader):
        """
        self.HashStart = reader.ReadSerializableArray('neocore.UInt256.UInt256')
        self.HashStop = reader.ReadUInt256()

    def Serialize(self, writer):
        """
        Serialize object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        writer.WriteHashes(self.HashStart)
        if self.HashStop is not None:
            writer.WriteUInt256(self.HashStop)
