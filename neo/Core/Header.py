# -*- coding: UTF-8 -*-

from neo.Core.BlockBase import BlockBase
from neo.IO.MemoryStream import MemoryStream, StreamManager
from neo.IO.BinaryReader import BinaryReader
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
        super(Header, self).Deserialize(reader)
        if reader.ReadByte() != 0:
            raise Exception('Incorrect Header Format')

    def Equals(self, other):

        if other is None:
            return False
        if other is self:
            return True
        return self.Hash == other.Hash

    @staticmethod
    def FromTrimmedData(data, index):

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
        return self.Hash

    def Serialize(self, writer):

        super(Header, self).Serialize(writer)
        writer.WriteByte(0)
