# -*- coding: UTF-8 -*-

from neo.Core.BlockBase import BlockBase
from neocore.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import StreamManager
from neo.Core.Witness import Witness


class Header(BlockBase):

    def __init__(self, prevhash=None, merlke_root=None, timestamp=None,
                 index=None, consensus_data=None, next_consenus=None, script=None):

        super(Header, self).__init__()

        self.PrevHash = prevhash
        self.MerkleRoot = merlke_root
        self.Timestamp = timestamp
        self.Index = index
        self.ConsensusData = consensus_data
        self.NextConsensus = next_consenus
        self.Script = script

    def Size(self):
        return super(Header, self).Size() + 1

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neo.IO.BinaryReader):
        """
        super(Header, self).Deserialize(reader)
        if reader.ReadByte() != 0:
            raise Exception('Incorrect Header Format')

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
        if other is self:
            return True
        return self.Hash == other.Hash

    @staticmethod
    def FromTrimmedData(data, index):
        """
        Deserialize into a Header object from the provided data.

        Args:
            data (bytes):
            index: UNUSED

        Returns:
            Header:
        """
        header = Header()

        ms = StreamManager.GetStream(data)

        reader = BinaryReader(ms)
        header.DeserializeUnsigned(reader)
        reader.ReadByte()

        witness = Witness()
        witness.Deserialize(reader)
        header.Script = witness

        StreamManager.ReleaseStream(ms)

        return header

    def GetHashCode(self):
        """
        Get the hash code of the header.

        Returns:
            UInt256:
        """
        return self.Hash

    def Serialize(self, writer):
        """
        Serialize full object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        super(Header, self).Serialize(writer)
        writer.WriteByte(0)
