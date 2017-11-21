from neo.IO.Mixins import SerializableMixin
from neo.Network.Payloads.NetworkAddressWithTime import NetworkAddressWithTime
from neo.Core.Blockchain import Blockchain

import sys
import ctypes
import datetime
from autologging import logged


@logged
class VersionPayload(SerializableMixin):

    Version = None
    Services = None
    Timestamp = None
    Port = None
    Nonce = None
    UserAgent = None
    StartHeight = 0
    Relay = False

    def __init__(self, port=None, nonce=None, userAgent=None):
        if port and nonce and userAgent:
            self.Port = port
            self.Version = 0
            self.Services = NetworkAddressWithTime.NODE_NETWORK
            self.Timestamp = int(datetime.datetime.utcnow().timestamp())
            self.Nonce = nonce
            self.UserAgent = userAgent

            if Blockchain.Default() is not None and Blockchain.Default().Height is not None:
                self.StartHeight = Blockchain.Default().Height

            self.Relay = True

    def Size(self):
        return ctypes.sizeof(ctypes.c_uint) + ctypes.sizeof(ctypes.c_ulong) + ctypes.sizeof(ctypes.c_uint) + \
            ctypes.sizeof(ctypes.c_ushort) + ctypes.sizeof(ctypes.c_uint) + \
            sys.getsizeof(self.UserAgent) + ctypes.sizeof(ctypes.c_uint) + ctypes.sizeof(ctypes.c_bool)

    def Deserialize(self, reader):
        self.__log.debug("DESERIALIZING VERSION!!!!")
        self.Version = reader.ReadUInt32()

        self.Services = reader.ReadUInt64()
        self.Timestamp = reader.ReadUInt32()
        self.Port = reader.ReadUInt16()
        self.Nonce = reader.ReadUInt32()
        self.UserAgent = reader.ReadVarString().decode('utf-8')
        self.StartHeight = reader.ReadUInt32()
        self.__log.debug("VERSION START HEIGH:T %s " % self.StartHeight)
        self.Relay = reader.ReadBool()

    def Serialize(self, writer):
        writer.WriteUInt32(self.Version)
        writer.WriteUInt64(self.Services)
        writer.WriteUInt32(self.Timestamp)
        writer.WriteUInt16(self.Port)
        writer.WriteUInt32(self.Nonce)
        writer.WriteVarString(self.UserAgent)
        writer.WriteUInt32(self.StartHeight)
        writer.WriteBool(self.Relay)
