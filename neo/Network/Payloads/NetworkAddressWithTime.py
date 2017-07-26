
from neo.IO.Mixins import SerializableMixin
import sys
import ctypes
from neo.Network.IPEndpoint import IPEndpoint

class NetworkAddressWithTime(SerializableMixin):

    NODE_NETWORK = 1

    Timestamp = None
    Services = None
    Endpoint = None

    def __init__(self, endpoint=None, services=None, timestamp=None):
        self.Endpoint = endpoint
        self.Services = services
        self.Timestamp = timestamp


    def Size(self):
        return ctypes.sizeof(ctypes.c_uint) + ctypes.sizeof(ctypes.c_ulong) + 16 + ctypes.sizeof(ctypes.c_ushort)


    def Deserialize(self, reader):
        self.Timestamp = reader.ReadUInt32()
        self.Services = reader.ReadUInt64()
        address =  reader.ReadBytes(16)
        port = int.from_bytes( reader.ReadBytes(2).reverse(), 'big')
        self.Endpoint = IPEndpoint(address, port)

    def Serialize(self, writer):
        writer.Write(self.Timestamp)
        writer.Write(self.Services)
        #writer.Write(EndPoint.Address.GetAddressBytes());
        #writer.Write(BitConverter.GetBytes((ushort)EndPoint.Port).Reverse().ToArray())

        writer.Write(self.Endpoint.Address)
        writer.Write(self.Endpoint.Port)


