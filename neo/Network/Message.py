from neo.IO.Mixins import SerializableMixin
from neo.IO.BinaryReader import BinaryReader
from neo.IO.BinaryWriter import BinaryWriter
from neo.IO.MemoryStream import MemoryStream
from neo import Settings
from neo.Core.Helper import Helper
from neo.Cryptography.Helper import *
import ctypes
import asyncio
import binascii
from autologging import logged

class ChecksumException(Exception):
    pass

@logged
class Message(SerializableMixin):


    PayloadMaxSize = b'\x02000000'
    PayloadMaxSizeInt = int.from_bytes(PayloadMaxSize, 'big')

    Magic = None

    Command = None

    Checksum = None

    Payload = None

    Length = 0


    def __init__(self, command=None, payload = None):

        self.Command = command
        self.Magic = Settings.MAGIC

        if payload is None:
            payload = bytearray()
        else:
            payload = binascii.unhexlify( Helper.ToArray(payload))

        self.Checksum = Message.GetChecksum(payload)
        self.Payload = payload

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

        self.__log.debug("Deserialized Message %s " % self.Command)

    @staticmethod
    def DeserializeFromAsyncStream(stream, cancellation_token):

        buffer = bytearray(24)

        raise NotImplementedError()


    @staticmethod
    def DeserializeFromAsyncSocket(socket, cancellation_token):
        buffer = bytearray(24)

        try:
            socket.recv_into(buffer, 24)

            ms = MemoryStream(buffer)
            reader = BinaryReader(ms)

            message = Message()

            message.Magic = reader.ReadUInt32()
            message.Command = reader.ReadFixedString(12).decode('utf-8')

            length = reader.ReadUInt32()

            if length > Message.PayloadMaxSizeInt:
                raise Exception("format too big")

            message.Checksum = reader.ReadUInt32()

            message.Payload = bytearray(length)

            if length > 0:
                message.Payload = Message.FillBufferAsyncStream(socket, length, None)

            checksum = Message.GetChecksum(message.Payload)

            if checksum != message.Checksum:

                print("Message command :%s " % message.Command)
                print("Checksum mismatch: %s " % message.Checksum)
                print("message payload: %s " % message.Payload)
                return None
                #raise Exception("invalid checksum")

            return message

        except Exception as e:
                print("could not receive buffer from socket: %s " % e)





    @staticmethod
    def FillBufferAsyncStream(stream, length, cancellation_token):
        chunks=[]
        bytes_received=0

        while bytes_received  < length:
            chunk = stream.recv(min(length - bytes_received, 1024))
            if chunk == b'':
                raise Exception('Socket connection broken')
            chunks.append(chunk)
            bytes_received = bytes_received + len(chunk)

        return b''.join(chunks)

    @staticmethod
    async def FillBufferAsyncSocket(socket, buffer, cancellation_token):
        raise NotImplementedError()



    @staticmethod
    def GetChecksum(value):

        uint32 = bin_dbl_sha256(value)[:4]

        return int.from_bytes( uint32, 'little')



    def Serialize(self, writer):

        writer.WriteUInt32(self.Magic)
        writer.WriteFixedString(self.Command, 12)
        writer.WriteUInt32(len(self.Payload))
        writer.WriteUInt32(self.Checksum)
        writer.WriteBytes(self.Payload)

