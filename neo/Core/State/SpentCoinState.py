# -*- coding:utf-8 -*-

from .StateBase import StateBase
from neo.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream,StreamManager
import binascii
from autologging import logged


class SpentCoinItem():
    index = None
    height = None

    def __init__(self, index, height):
        self.index = index
        self.height = height




@logged
class SpentCoinState(StateBase):
    Output = None
    StartHeight = None
    EndHeight = None


    TransactionHash = None
    TransactionHeight = None
    Items = []

    def __init__(self, hash=None, height = None, items = []):
        self.TransactionHash = hash
        self.TransactionHeight = height
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
#        print("reading count %s " % count)
        items = [0] * count
        for i in range(0, count):
            index = reader.ReadUInt16()
#            print("read index %s " % index)
            height = reader.ReadUInt32()
#            print("read height %s" % height)
            items[i] = SpentCoinItem(index=index, height=height)

        self.Items = items


    def Serialize(self, writer):

        super(SpentCoinState, self).Serialize(writer)

        writer.WriteUInt256(self.TransactionHash)
        writer.WriteUInt32(self.TransactionHeight)

        writer.WriteVarInt( len( self.Items))

        for item in self.Items:
            writer.WriteUInt16(item.index)
            writer.WriteUInt32(item.height)



    def ToJson(self):

        items = []

        ba = bytearray(self.TransactionHash)
        txhash = binascii.hexlify(ba)

        for i in self.Items:
            items.append({'index': i.index, 'height':i.height})

        return {
            'version':self.StateVersion,
            'txHash': txhash.decode('utf-8'),
            'txHeight': self.TransactionHeight,
            'items': items
        }
