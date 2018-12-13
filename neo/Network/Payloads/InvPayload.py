import binascii
from neocore.UInt256 import UInt256
from neocore.IO.Mixins import SerializableMixin
from neo.Core.Size import Size as s
from neo.Core.Size import GetVarSize
from neo.logging import log_manager

logger = log_manager.getLogger()


class InvPayload(SerializableMixin):
    Type = None
    Hashes = []

    def __init__(self, type=None, hashes=None):
        """
        Create an instance.

        Args:
            type (neo.Network.InventoryType):
            hashes (list): of bytearray items.
        """
        self.Type = type
        self.Hashes = hashes if hashes else []

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        if len(self.Hashes) > 0:
            if not isinstance(self.Hashes[0], UInt256):
                corrected_hashes = list(map(lambda i: UInt256(data=binascii.unhexlify(i)), self.Hashes))
        return s.uint8 + GetVarSize(corrected_hashes)

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neo.IO.BinaryReader):
        """
        self.Type = reader.ReadByte()
        self.Hashes = reader.ReadHashes()

    def Serialize(self, writer):
        """
        Serialize object.

        Raises:
            Exception: if hash writing fails.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        try:
            writer.WriteByte(self.Type)
            writer.WriteHashes(self.Hashes)
        except Exception as e:
            logger.error(f"COULD NOT WRITE INVENTORY HASHES ({self.Type} {self.Hashes}) {e}")

    def ToString(self):
        """
        Get the string representation of the payload.

        Returns:
            str:
        """
        return "INVENTORY Type %s hashes %s " % (self.Type, [h for h in self.Hashes])
