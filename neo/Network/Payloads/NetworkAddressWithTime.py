import ctypes
from datetime import datetime
from neocore.IO.Mixins import SerializableMixin
from neo.Core.Size import Size as s


class NetworkAddressWithTime(SerializableMixin):
    NODE_NETWORK = 1

    Timestamp = None
    Services = None
    Address = None
    Port = None

    def __init__(self, address=None, port=None, services=0, timestamp=int(datetime.utcnow().timestamp())):
        """
        Create an instance.

        Args:
            address (str):
            port (int):
            services (int):
            timestamp (int):
        """
        self.Address = address
        self.Port = port
        self.Services = services
        self.Timestamp = timestamp

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        return s.uint32 + s.uint64 + 16 + s.uint16

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neo.IO.BinaryReader):
        """
        self.Timestamp = reader.ReadUInt32()
        self.Services = reader.ReadUInt64()
        addr = bytearray(reader.ReadFixedString(16))
        addr.reverse()
        addr.strip(b'\x00')
        nums = []
        for i in range(0, 4):
            nums.append(str(addr[i]))
        nums.reverse()
        adddd = '.'.join(nums)
        self.Address = adddd
        self.Port = reader.ReadUInt16(endian='>')

    def Serialize(self, writer):
        """
        Serialize object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        writer.WriteUInt32(self.Timestamp)
        writer.WriteUInt64(self.Services)
        # turn ip address into bytes
        octets = bytearray(map(lambda oct: int(oct), self.Address.split('.')))
        # pad to fixed length 16
        octets += bytearray(12)
        # and finally write to stream
        writer.WriteBytes(octets)
        writer.WriteUInt16(self.Port, endian='>')

    def ToString(self):
        """
        Get the string representation of the network address.

        Returns:
            str: address:port
        """
        return '%s:%s' % (self.Address, self.Port)
