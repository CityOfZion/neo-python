import sys
import ctypes
from datetime import datetime

from neo.Network.IPEndpoint import IPEndpoint
from neo.IO.Mixins import SerializableMixin


class NetworkAddressWithTime(SerializableMixin):

    NODE_NETWORK = 1

    Timestamp = None
    Services = None
    Address = None
    Port = None

    def __init__(self, address=None, port=None, services=0, timestamp=int(datetime.utcnow().timestamp())):
        self.Address = address
        self.Port = port
        self.Services = services
        self.Timestamp = timestamp

    def Size(self):
        return ctypes.sizeof(ctypes.c_uint) + ctypes.sizeof(ctypes.c_ulong) + 16 + ctypes.sizeof(ctypes.c_ushort)

    def Deserialize(self, reader):
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
        writer.WriteUInt32(self.Timestamp)
        writer.WriteUInt64(self.Services)
        writer.WriteFixedString(self.Address, 16)
        writer.WriteUInt16(self.Port, endian='>')

    def ToString(self):
        return '%s:%s' % (self.Address, self.Port)
