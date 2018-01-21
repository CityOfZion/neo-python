from .StateBase import StateBase
from neocore.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import StreamManager


class StorageItem(StateBase):
    Value = None

    def __init__(self, value=None):
        """
        Create an instance.

        Args:
            value (bytearray): value to store.
        """
        if value is None:
            self.Value = bytearray(0)
        else:
            self.Value = value

    def Clone(self):
        """
        Clone self.

        Returns:
            StorageItem:
        """
        return StorageItem(value=self.Value)

    def FromReplica(self, replica):
        """
        Get StorageItem object from a replica.
        Args:
            replica (obj): must have `Value` member.

        Returns:
            StorageItem:
        """
        self.Value = replica.Value

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        return super(StorageItem, self).Size() + len(self.Value)

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neocore.IO.BinaryReader):
        """
        super(StorageItem, self).Deserialize(reader)
        self.Value = reader.ReadVarBytes()

    @staticmethod
    def DeserializeFromDB(buffer):
        """
        Deserialize full object.

        Args:
            buffer (bytes, bytearray, BytesIO): (Optional) data to create the stream from.

        Returns:
            StorageItem:
        """
        m = StreamManager.GetStream(buffer)
        reader = BinaryReader(m)
        v = StorageItem()
        v.Deserialize(reader)
        StreamManager.ReleaseStream(m)
        return v

    def Serialize(self, writer):
        """
        Serialize full object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        super(StorageItem, self).Serialize(writer)
        writer.WriteVarBytes(self.Value)
