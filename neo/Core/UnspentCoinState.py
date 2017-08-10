
from .StateBase import StateBase
import sys
from neo.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream

class UnspentCoinState(StateBase):


    Items = {}

    def __init__(self, items={}):
        self.Items = items

    def Size(self):
        return super(UnspentCoinState, self).Size() + sys.getsizeof(self.Items)

    def Deserialize(self, reader):
        super(UnspentCoinState, self).Deserialize(reader)
        self.Items = bytearray(reader.ReadVarBytes())

    @staticmethod
    def DeserializeFromDB(buffer):
        m = MemoryStream(buffer)
        reader = BinaryReader(m)
        uns = UnspentCoinState()
        uns.Deserialize(reader)
        return uns

    def Serialize(self, writer):
        super(UnspentCoinState, self).Serialize(writer)
        writer.WriteVarBytes(self.Items, unhexlify=False)
