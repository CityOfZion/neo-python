from neo.IO.Mixins import SerializableMixin
from neo import Settings
from neo.Cryptography.Helper import *
import ctypes

class Message(SerializableMixin):


    PayloadMaxSize = b'\x02000000'

    Magic = Settings.MAGIC

    Command = None

    Checksum = None

    Payload = None


    def __init__(self, command, payload = None):

        self.Command = command

        if payload is None:
            payload = bytearray()

        self.Checksum = Message.GetChecksum(payload)

        self.Payload = payload


    def Size(self):
        return ctypes.sizeof(ctypes.c_uint) + 12 + ctypes.sizeof(ctypes.c_int) + ctypes.sizeof(ctypes.c_uint) + len(self.Payload)

    def Deserialize(self, reader):
        if reader.ReadUInt32() != self.Magic:
            raise Exception("Invalit format, wrong magic")

        self.Command = reader.ReadFixedString(12)

        length = reader.ReadUInt32()

        if length > self.PayloadMaxSize:
            raise Exception("invalid format- payload too large")

        self.Checksum = reader.ReadUInt32()

        self.Payload = reader.ReadBytes(length)

        if not Message.GetChecksum(self.Payload) != self.Checksum:
            raise Exception("checksum mismatch")

    @staticmethod
    def DeserializeFromAsyncStream(stream, cancellation_token):

        buffer = bytearray(24)

        raise NotImplementedError()


    @staticmethod
    def DeserializeFromAsyncSocket(socket, cancellation_token):
        buffer = bytearray(24)

        raise NotImplementedError()


    @staticmethod
    def FillBufferAsyncStream(stream, buffer, cancellation_token):
        raise NotImplementedError()

    @staticmethod
    def FillBufferAsyncSocket(socket, buffer, cancellation_token):
        raise NotImplementedError()



    @staticmethod
    def GetChecksum(value):
        return int.from_bytes( bin_sha256(value), 'big')



    def Serialize(self, writer):

        writer.Write(self.Magic)
        writer.WriteFixedString(self.Command, 12)
        writer.Write(len(self.Payload))
        writer.Write(self.Checksum)
        writer.Write(self.Payload)

