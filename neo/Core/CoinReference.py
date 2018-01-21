# -*- coding: UTF-8 -*-

import sys


class CoinReference(object):
    PrevHash = None

    PrevIndex = None

    def __init__(self, prev_hash=None, prev_index=None):
        """
        Create an instance.

        Args:
            prev_hash (UInt256): hash of the previous output.
            prev_index (int):
        """
        self.PrevHash = prev_hash
        self.PrevIndex = prev_index

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        return sys.getsizeof(self.PrevHash) + sys.getsizeof(int)

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neo.IO.BinaryReader):
        """
        self.PrevHash = reader.ReadUInt256()
        self.PrevIndex = reader.ReadUInt16()

    def Serialize(self, writer):
        """
        Serialize full object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        writer.WriteUInt256(self.PrevHash)
        writer.WriteUInt16(self.PrevIndex)

    def Equals(self, other):
        """
        Test for equality.

        Args:
            other (obj):

        Returns:
            bool: True `other` equals self.
        """
        if other is None:
            return False
        if other.PrevHash.ToBytes() == self.PrevHash.ToBytes() and other.PrevIndex == self.PrevIndex:
            return True
        return False

    def __eq__(self, other):
        if other is None:
            return False
        if other.PrevHash.ToBytes() == self.PrevHash.ToBytes() and other.PrevIndex == self.PrevIndex:
            return True
        return False

    def __hash__(self):
        return int.from_bytes(self.PrevHash.ToBytes(), 'little') + self.PrevIndex

    def ToJson(self):
        """
        Convert object members to a dictionary that can be parsed as JSON.

        Returns:
             dict:
        """
        out = {
            'txid': self.PrevHash.ToString(),
            'vout': self.PrevIndex
        }

        return out
