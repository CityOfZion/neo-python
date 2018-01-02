from collections import namedtuple
from .StateBase import StateBase
from neocore.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import StreamManager


class SpentCoinItem():
    index = None
    height = None

    def __init__(self, index, height):
        """
        Create an instance.

        Args:
            index (int):
            height (int):
        """
        self.index = index
        self.height = height


class SpentCoin():
    Output = None
    StartHeight = None
    EndHeight = None

    @property
    def Value(self):
        """
        Get the coin output value.

        Returns:
            int.
        """
        return self.Output.Value

    @property
    def Heights(self):
        """
        Get the coin heights.

        Returns:
            namedtuple:
        """
        CoinHeight = namedtuple("CoinHeight", "start end")
        return CoinHeight(self.StartHeight, self.EndHeight)

    def __init__(self, output, start_height, end_height):
        """
        Create instance.

        Args:
            output (int): the index of the previous output.
            start_height (int): start block number.
            end_height (int): end block number.
        """
        self.Output = output
        self.StartHeight = start_height
        self.EndHeight = end_height

    def ToJson(self):
        """
        Convert object members to a dictionary that can be parsed as JSON.

        Returns:
             dict:
        """
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
        """
        Create an instance.

        Args:
            hash (UInt256):
            height (int):
            items (list):
        """
        self.TransactionHash = hash
        self.TransactionHeight = height
        if items is None:
            self.Items = []
        else:
            self.Items = items

    def HasIndex(self, index):
        """
        Flag indicating the index exists in any of the spent coin items.
        Args:
            index (int):

        Returns:

        """
        for i in self.Items:
            if i.index == index:
                return True
        return False

    def DeleteIndex(self, index):
        """
        Remove a spent coin based on its index.

        Args:
            index (int):
        """
        to_remove = None
        for i in self.Items:
            if i.index == index:
                to_remove = i

        if to_remove:
            self.Items.remove(to_remove)

    @staticmethod
    def DeserializeFromDB(buffer):
        """
        Deserialize full object.

        Args:
            buffer (bytes, bytearray, BytesIO): (Optional) data to create the stream from.

        Returns:
            SpentCoinState:
        """
        m = StreamManager.GetStream(buffer)
        reader = BinaryReader(m)
        spentcoin = SpentCoinState()
        spentcoin.Deserialize(reader)

        StreamManager.ReleaseStream(m)

        return spentcoin

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neocore.IO.BinaryReader):
        """
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
        """
        Serialize full object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        super(SpentCoinState, self).Serialize(writer)

        writer.WriteUInt256(self.TransactionHash)
        writer.WriteUInt32(self.TransactionHeight)
        writer.WriteVarInt(len(self.Items))

        for item in self.Items:
            writer.WriteUInt16(item.index)
            writer.WriteUInt32(item.height)

    def ToJson(self):
        """
        Convert object members to a dictionary that can be parsed as JSON.

        Returns:
             dict:
        """
        items = []

        for i in self.Items:
            items.append({'index': i.index, 'height': i.height})

        return {
            'version': self.StateVersion,
            'txHash': self.TransactionHash.ToString(),
            'txHeight': self.TransactionHeight,
            'items': items
        }
