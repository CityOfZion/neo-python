# -*- coding:utf-8 -*-

from .StateBase import StateBase
from neo.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream

class SpentCoinState(StateBase):
    Output = None
    StartHeight = None
    EndHeight = None


    TransactionHash = None
    TransactionHeight = None
    Items = {}

    def __init__(self, hash=None, height = None, items = {}):
        self.TransactionHash = hash
        self.TransactionHeight = height
        self.Items = items

    @staticmethod
    def DeserializeFromDB(buffer):
        m = MemoryStream(buffer)
        reader = BinaryReader(m)
        spentcoin = SpentCoinState()
        spentcoin.Deserialize(reader)
        return spentcoin

    def Deserialize(self, reader):
        self.TransactionHash = reader.ReadUInt256()
        self.TransactionHeight = reader.ReadUInt32()

        count = reader.ReadVarInt()
        items = {}
        for i in range(0, count):
            items[ reader.ReadUInt16()] = reader.ReadUInt32()

        self.Items = items


    def Serialize(self, writer):

        super(SpentCoinState, self).Serialize(writer)

        writer.WriteUInt256(self.TransactionHash)
        writer.WriteUInt32(self.TransactionHeight)

        writer.WriteVarInt( len( self.Items))

        for key,val in self.Items:
            writer.WriteUInt16(key)
            writer.WriteUInt32(val)

            