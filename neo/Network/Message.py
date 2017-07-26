from neo.IO.Mixins import SerializableMixin
from neo.IO.BinaryReader import BinaryReader
from neo.IO.BinaryWriter import BinaryWriter
from neo.IO.MemoryStream import MemoryStream
from neo import Settings
from neo.Cryptography.Helper import *
import ctypes
import asyncio

class Message(SerializableMixin):


    PayloadMaxSize = b'\x02000000'

    Magic = Settings.MAGIC

    Command = None

    Checksum = None

    Payload = None


    def __init__(self, command=None, payload = None):

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
    async def DeserializeFromAsyncSocket(socket, cancellation_token):
        buffer = bytearray(24)

        try:
            socket.recv_into(buffer, 24)

            ms = MemoryStream(buffer)
            reader = BinaryReader(ms)

            message = Message()
            message.Command = reader.ReadFixedString(12)
            length = reader.ReadUInt32()
            if length > Message.PayloadMaxSize:
                raise Exception("format too big")

            message.Checksum = reader.ReadUInt32()
            message.Payload = bytearray(length)

            if len(message.Payload) > 0:
                socket.recv_into(message.Payload)

            checksum = Message.GetChecksum(message.Payload)

            if checksum != message.Checksum:
                raise Exception("checksum mismatch")


        except Exception as e:
                print("could not receive buffer from socket: %s " % e)




        raise NotImplementedError()


    @staticmethod
    def FillBufferAsyncStream(stream, buffer, cancellation_token):
        raise NotImplementedError()

    @staticmethod
    async def FillBufferAsyncSocket(socket, buffer, cancellation_token):
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

