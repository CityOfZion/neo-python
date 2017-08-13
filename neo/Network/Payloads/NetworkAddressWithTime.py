
from neo.IO.Mixins import SerializableMixin
import sys
import ctypes
from neo.Network.IPEndpoint import IPEndpoint

class NetworkAddressWithTime(SerializableMixin):

    NODE_NETWORK = 1

    Timestamp = None
    Services = None
    Address = None
    Port = None

    def __init__(self, address=None, port=None, services=None, timestamp=None):
        self.Address = address
        self.Port = port
        self.Services = services
        self.Timestamp = timestamp


    def Size(self):
        return ctypes.sizeof(ctypes.c_uint) + ctypes.sizeof(ctypes.c_ulong) + 16 + ctypes.sizeof(ctypes.c_ushort)


    def Deserialize(self, reader):
        self.Timestamp = reader.ReadUInt32()
        self.Services = reader.ReadUInt64()
        self.Address =  reader.ReadFixedString(16).decode('utf-8')
        self.Port = reader.ReadUInt16(endian='>')

    def Serialize(self, writer):
        writer.WriteUInt32(self.Timestamp)
        writer.WriteUInt64(self.Services)
        writer.WriteFixedString(self.Address,16)
        writer.WriteUInt16(self.Port, endian='>')


