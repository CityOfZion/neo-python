
from neo.IO.Mixins import SerializableMixin
from neo.Network.LocalNode import LocalNode
from neo.Network.Payloads.NetworkAddressWithTime import NetworkAddressWithTime
from neo.Core.Blockchain import Blockchain

import sys
import ctypes
import datetime


class VersionPayload(SerializableMixin):

    Version=None
    Services = None
    Timestamp = None
    Port = None
    Nonce = None
    UserAgent = None
    StartHeight = None
    Relay = False

    def __init__(self, port=None, nonce=None, userAgent=None):
        if port and nonce and userAgent:
            self.Version = LocalNode.PROTOCOL_VERSION
            self.Services = NetworkAddressWithTime.NODE_NETWORK
            self.Timestamp = datetime.datetime.utcnow()
            self.Nonce = nonce
            self.UserAgent = userAgent
            self.StartHeight = Blockchain.Default().Height()
            self.Relay = True

    def Size(self):
        return ctypes.sizeof(ctypes.c_uint) + ctypes.sizeof(ctypes.c_ulong) + ctypes.sizeof(ctypes.c_uint) + \
                ctypes.sizeof(ctypes.c_ushort) + ctypes.sizeof(ctypes.c_uint) + \
                  sys.getsizeof(self.UserAgent) + ctypes.sizeof(ctypes.c_uint) + ctypes.sizeof(ctypes.c_bool)


    def Deserialize(self, reader):
        self.Version = reader.ReadUInt32()
        self.Services = reader.ReadUInt64()
        self.Timestamp = reader.ReadUInt32()
        self.Port = reader.ReadUInt16()
        self.Nonce = reader.ReadUInt32()
        self.UserAgent = reader.ReadVarString(1024)
        self.StartHeight = reader.ReadUInt32()
        self.Relay = reader.ReadBoolean()

    def Serialize(self, writer):
        writer.Write(self.Version)
        writer.Write(self.Services)
        writer.Write(self.Timestamp)
        writer.Write(self.Port)
        writer.Write(self.Nonce)
        writer.WriteVarString(self.UserAgent)
        writer.Write(self.StartHeight)
        writer.Write(self.Relay)