
from .StateBase import StateBase
import sys
from neo.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream, StreamManager
from .CoinState import CoinState
from autologging import logged


@logged
class UnspentCoinState(StateBase):

    Items = None

    def __init__(self, items=None):
        if items is None:
            self.Items = []
        else:
            self.Items = items

    @staticmethod
    def FromTXOutputsConfirmed(outputs):
        uns = UnspentCoinState()
        uns.Items = [0] * len(outputs)
        for i in range(0, len(outputs)):
            uns.Items[i] = CoinState.Confirmed
        return uns

    def Size(self):
        return super(UnspentCoinState, self).Size() + sys.getsizeof(self.Items)

    def IsAllSpent(self):
        for item in self.Items:
            if item & CoinState.Spent > 0:
                return False
        return True

    def OrEqValueForItemAt(self, index, value):

        length = len(self.Items)

        while length < index + 1:
            self.Items.append(0)
            length = len(self.Items)

        self.Items[index] |= value

    def Deserialize(self, reader):
        super(UnspentCoinState, self).Deserialize(reader)

        blen = reader.ReadVarInt()
        self.Items = [0] * blen
        for i in range(0, blen):
            self.Items[i] = reader.ReadByte()

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

        [writer.WriteByte(item) for item in self.Items]
