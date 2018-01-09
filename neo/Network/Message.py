import ctypes
from neocore.IO.Mixins import SerializableMixin
from neo.Settings import settings
from neo.Core.Helper import Helper
from neocore.Cryptography.Helper import *


class ChecksumException(Exception):
    pass


class Message(SerializableMixin):
    PayloadMaxSize = b'\x02000000'
    PayloadMaxSizeInt = int.from_bytes(PayloadMaxSize, 'big')

    Magic = None

    Command = None

    Checksum = None

    Payload = None

    Length = 0

    def __init__(self, command=None, payload=None, print_payload=False):
        """
        Create an instance.

        Args:
            command (str): payload command i.e. "inv", "getdata". See NeoNode.MessageReceived() for more commands.
            payload (bytes): raw bytes of the payload.
            print_payload: UNUSED
        """
        self.Command = command
        self.Magic = settings.MAGIC

        if payload is None:
            payload = bytearray()
        else:
            payload = binascii.unhexlify(Helper.ToArray(payload))

        self.Checksum = Message.GetChecksum(payload)
        self.Payload = payload

    #        if print_payload:
    #            logger.info("PAYLOAD: %s " % self.Payload)

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        return ctypes.sizeof(ctypes.c_uint) + 12 + ctypes.sizeof(ctypes.c_int) + ctypes.sizeof(ctypes.c_uint) + len(
            self.Payload)

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neo.IO.BinaryReader):
        """
        self.Magic = reader.ReadUInt32()
        self.Command = reader.ReadFixedString(12).decode('utf-8')
        self.Length = reader.ReadUInt32()

        if self.Length > self.PayloadMaxSizeInt:
            raise Exception("invalid format- payload too large")

        self.Checksum = reader.ReadUInt32()
        self.Payload = reader.ReadBytes(self.Length)

        checksum = Message.GetChecksum(self.Payload)

        if checksum != self.Checksum:
            raise ChecksumException("checksum mismatch")

    @staticmethod
    def GetChecksum(value):
        """
        Get the double SHA256 hash of the value.

        Args:
            value (obj): a payload

        Returns:

        """
        uint32 = bin_dbl_sha256(value)[:4]

        return int.from_bytes(uint32, 'little')

    def Serialize(self, writer):
        """
        Serialize object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        writer.WriteUInt32(self.Magic)
        writer.WriteFixedString(self.Command, 12)
        writer.WriteUInt32(len(self.Payload))
        writer.WriteUInt32(self.Checksum)
        writer.WriteBytes(self.Payload)
