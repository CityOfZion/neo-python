from neocore.IO.Mixins import SerializableMixin
import sys


class AddrPayload(SerializableMixin):
    NetworkAddressesWithTime = []

    def __init__(self, addresses=None):
        """
        Create an instance.

        Args:
            addresses (list): of neo.Network.Payloads.NetworkAddressWithTime.NetworkAddressWithTime instances.
        """
        self.NetworkAddressesWithTime = addresses if addresses else []

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        return sys.getsizeof(self.NetworkAddressesWithTime)

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neocore.IO.BinaryReader):
        """
        self.NetworkAddressesWithTime = reader.ReadSerializableArray(
            'neo.Network.Payloads.NetworkAddressWithTime.NetworkAddressWithTime')

    def Serialize(self, writer):
        """
        Serialize object.

        Args:
            writer (neocore.IO.BinaryWriter):
        """
        writer.WriteVarInt(len(self.NetworkAddressesWithTime))
        for address in self.NetworkAddressesWithTime:
            address.Serialize(writer)
