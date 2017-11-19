import ctypes
import asyncio
import binascii
import pympler

from logzero import logger

from neo.IO.Mixins import SerializableMixin
from neo.IO.BinaryReader import BinaryReader
from neo.IO.BinaryWriter import BinaryWriter
from neo.IO.MemoryStream import MemoryStream, StreamManager
from neo.Settings import settings
from neo.Core.Helper import Helper
from neo.Cryptography.Helper import *


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
        return ctypes.sizeof(ctypes.c_uint) + 12 + ctypes.sizeof(ctypes.c_int) + ctypes.sizeof(ctypes.c_uint) + len(self.Payload)

    def Deserialize(self, reader):
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

#        logger.info("Deserialized Message %s " % self.Command)

    @staticmethod
    def GetChecksum(value):

        uint32 = bin_dbl_sha256(value)[:4]

        return int.from_bytes(uint32, 'little')

    def Serialize(self, writer):

        writer.WriteUInt32(self.Magic)
        writer.WriteFixedString(self.Command, 12)
        writer.WriteUInt32(len(self.Payload))
        writer.WriteUInt32(self.Checksum)
        writer.WriteBytes(self.Payload)
