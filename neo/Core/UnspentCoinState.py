
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

        item_array = bytearray(reader.ReadVarBytes())
        for i in range(0, len(item_array)):
            self.Items[i] = item_array[i]
        print("item dict: %s " % self.Items)

    @staticmethod
    def DeserializeFromDB(buffer):
        m = MemoryStream(buffer)
        reader = BinaryReader(m)
        uns = UnspentCoinState()
        uns.Deserialize(reader)
        return uns

    def Serialize(self, writer):
        super(UnspentCoinState, self).Serialize(writer)
        items = [val for key,val in self.Items]
        writer.WriteVarBytes(self.Items, unhexlify=False)
