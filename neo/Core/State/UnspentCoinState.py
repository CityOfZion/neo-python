
from .StateBase import StateBase
import sys
from neo.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream,StreamManager
from .CoinState import CoinState

class UnspentCoinState(StateBase):


    Items = {}

    def __init__(self, items={}):
        self.Items = items

    @staticmethod
    def FromTXOutputsConfirmed(outputs):
        uns = UnspentCoinState()
        for i in range(0, len(outputs)):
            uns.Items[i] = CoinState.Confirmed
        return uns

    def Size(self):
        return super(UnspentCoinState, self).Size() + sys.getsizeof(self.Items)

    def IsAllSpent(self):
        for k,v in self.Items:
            if v & CoinState.Spent > 0:
                return False
        return True

    def Deserialize(self, reader):
        super(UnspentCoinState, self).Deserialize(reader)

        item_array = bytearray(reader.ReadVarBytes())
        for i in range(0, len(item_array)):
            self.Items[i] = item_array[i]

    @staticmethod
    def DeserializeFromDB(buffer):
        m = StreamManager.GetStream(buffer)
        reader = BinaryReader(m)
        uns = UnspentCoinState()
        uns.Deserialize(reader)

        StreamManager.ReleaseStream(m)

        return uns

    def Serialize(self, writer):
        super(UnspentCoinState, self).Serialize(writer)


        writer.WriteVarInt(len(self.Items))
        [writer.WriteByte(val) for key, val in self.Items.items()]
#items = [val for key,val in self.Items.items()]
#        print("serializing unspent coins!")
#        writer.WriteVarBytes(items, unhexlify=False)
