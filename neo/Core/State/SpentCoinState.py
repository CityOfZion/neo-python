import binascii
from collections import namedtuple

from .StateBase import StateBase

from neo.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream, StreamManager


class SpentCoinItem():
    index = None
    height = None

    def __init__(self, index, height):
        self.index = index
        self.height = height


class SpentCoin():

    Output = None
    StartHeight = None
    EndHeight = None

    @property
    def Value(self):
        return self.Output.Value

    @property
    def Heights(self):
        CoinHeight = namedtuple("CoinHeight", "start end")
        return CoinHeight(self.StartHeight, self.EndHeight)

    def __init__(self, output, start_height, end_height):
        self.Output = output
        self.StartHeight = start_height
        self.EndHeight = end_height

    def ToJson(self):
        return {
            'output': self.Output.ToJson(),
            'start': self.StartHeight,
            'end': self.EndHeight
        }


class SpentCoinState(StateBase):
    Output = None
    StartHeight = None
    EndHeight = None

    TransactionHash = None
    TransactionHeight = None
    Items = []

    def __init__(self, hash=None, height=None, items=None):
        self.TransactionHash = hash
        self.TransactionHeight = height
        if items is None:
            self.Items = []
        else:
            self.Items = items

    def HasIndex(self, index):
        for i in self.Items:
            if i.index == index:
                return True
        return False

    def DeleteIndex(self, index):
        to_remove = None
        for i in self.Items:
            if i.index == index:
                to_remove = i

        if to_remove:
            self.Items.remove(to_remove)

    @staticmethod
    def DeserializeFromDB(buffer):
        m = StreamManager.GetStream(buffer)
        reader = BinaryReader(m)
        spentcoin = SpentCoinState()
        spentcoin.Deserialize(reader)

        StreamManager.ReleaseStream(m)

        return spentcoin

    def Deserialize(self, reader):
        super(SpentCoinState, self).Deserialize(reader)

        self.TransactionHash = reader.ReadUInt256()
        self.TransactionHeight = reader.ReadUInt32()

        count = reader.ReadVarInt()

        items = [0] * count
        for i in range(0, count):
            index = reader.ReadUInt16()
            height = reader.ReadUInt32()
            items[i] = SpentCoinItem(index=index, height=height)

        self.Items = items

    def Serialize(self, writer):

        super(SpentCoinState, self).Serialize(writer)

        writer.WriteUInt256(self.TransactionHash)
        writer.WriteUInt32(self.TransactionHeight)

        writer.WriteVarInt(len(self.Items))

        for item in self.Items:
            writer.WriteUInt16(item.index)
            writer.WriteUInt32(item.height)

    def ToJson(self):

        items = []

        for i in self.Items:
            items.append({'index': i.index, 'height': i.height})

        return {
            'version': self.StateVersion,
            'txHash': self.TransactionHash.ToString(),
            'txHeight': self.TransactionHeight,
            'items': items
        }
