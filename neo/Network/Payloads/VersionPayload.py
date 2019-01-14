import datetime
from neocore.IO.Mixins import SerializableMixin
from neo.Network.Payloads.NetworkAddressWithTime import NetworkAddressWithTime
from neo.Core.Blockchain import Blockchain
from neo.Core.Size import Size as s
from neo.Core.Size import GetVarSize
from neo.logging import log_manager

logger = log_manager.getLogger()


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
        """
        Create an instance.

        Args:
            port (int):
            nonce (int):
            userAgent (str): client user agent string.
        """
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
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        return s.uint32 + s.uint64 + s.uint32 + s.uint16 + s.uint32 + GetVarSize(self.UserAgent) + s.uint32 + s.uint8

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neo.IO.BinaryReader):
        """
        self.Version = reader.ReadUInt32()
        self.Services = reader.ReadUInt64()
        self.Timestamp = reader.ReadUInt32()
        self.Port = reader.ReadUInt16()
        self.Nonce = reader.ReadUInt32()
        self.UserAgent = reader.ReadVarString().decode('utf-8')
        self.StartHeight = reader.ReadUInt32()
        logger.debug("Version start height: T %s " % self.StartHeight)
        self.Relay = reader.ReadBool()

    def Serialize(self, writer):
        """
        Serialize object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        writer.WriteUInt32(self.Version)
        writer.WriteUInt64(self.Services)
        writer.WriteUInt32(self.Timestamp)
        writer.WriteUInt16(self.Port)
        writer.WriteUInt32(self.Nonce)
        writer.WriteVarString(self.UserAgent)
        writer.WriteUInt32(self.StartHeight)
        writer.WriteBool(self.Relay)
