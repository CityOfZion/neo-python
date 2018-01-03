import sys
from .StateBase import StateBase
from .CoinState import CoinState
from neocore.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import StreamManager


class UnspentCoinState(StateBase):
    Items = None

    def __init__(self, items=None):
        """
        Create an instance.

        Args:
            items (list, Optional): of neo.Core.TX.Transaction.TransactionOutput items.
        """
        if items is None:
            self.Items = []
        else:
            self.Items = items

    @staticmethod
    def FromTXOutputsConfirmed(outputs):
        """
        Get unspent outputs from a list of transaction outputs.

        Args:
            outputs (list): of neo.Core.TX.Transaction.TransactionOutput items.

        Returns:
            UnspentCoinState:
        """
        uns = UnspentCoinState()
        uns.Items = [0] * len(outputs)
        for i in range(0, len(outputs)):
            uns.Items[i] = int(CoinState.Confirmed)
        return uns

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        return super(UnspentCoinState, self).Size() + sys.getsizeof(self.Items)

    @property
    def IsAllSpent(self):
        """
        Flag indicating if all balance is spend.

        Returns:
            bool:
        """
        for item in self.Items:
            if item == CoinState.Confirmed:
                return False
        return True

    def OrEqValueForItemAt(self, index, value):
        length = len(self.Items)
        while length < index + 1:
            self.Items.append(0)
            length = len(self.Items)

        self.Items[index] |= value

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neocore.IO.BinaryReader):
        """
        super(UnspentCoinState, self).Deserialize(reader)

        blen = reader.ReadVarInt()
        self.Items = [0] * blen
        for i in range(0, blen):
            self.Items[i] = int.from_bytes(reader.ReadByte(do_ord=False), 'little')

    @staticmethod
    def DeserializeFromDB(buffer):
        """
        Deserialize full object.

        Args:
            buffer (bytes, bytearray, BytesIO): (Optional) data to create the stream from.

        Returns:
            UnspentCoinState:
        """
        m = StreamManager.GetStream(buffer)
        reader = BinaryReader(m)
        uns = UnspentCoinState()
        uns.Deserialize(reader)

        StreamManager.ReleaseStream(m)

        return uns

    def Serialize(self, writer):
        """
        Serialize full object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        super(UnspentCoinState, self).Serialize(writer)

        writer.WriteVarInt(len(self.Items))

        for item in self.Items:
            byt = item.to_bytes(1, 'little')
            writer.WriteByte(byt)
