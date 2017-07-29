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

class Message(SerializableMixin):


    PayloadMaxSize = b'\x02000000'
    PayloadMaxSizeInt = int.from_bytes(PayloadMaxSize, 'big')

    Magic = None

    Command = None

    Checksum = None

    Payload = None


    def __init__(self, command=None, payload = None):

        self.Command = command
        self.Magic = Settings.MAGIC

        if payload is None:
            payload = bytearray()
        else:
            payload = binascii.unhexlify( Helper.ToArray(payload))

        print("created message, payload is : %s " % payload)
        self.Checksum = Message.GetChecksum(payload)
        print("created message, checksum: %s " % self.Checksum)
        self.Payload = payload


    def Size(self):
        return ctypes.sizeof(ctypes.c_uint) + 12 + ctypes.sizeof(ctypes.c_int) + ctypes.sizeof(ctypes.c_uint) + len(self.Payload)

    def Deserialize(self, reader):
        if reader.ReadUInt32() != self.Magic:
            raise Exception("Invalit format, wrong magic")

        self.Command = reader.ReadFixedString(12).decode('utf-8')

        length = reader.ReadUInt32()

        if length > self.PayloadMaxSizeInt:
            raise Exception("invalid format- payload too large")

        self.Checksum = reader.ReadUInt32()

        self.Payload = reader.ReadBytes(length)


        if not Message.GetChecksum(self.Payload) == self.Checksum:
            raise Exception("checksum mismatch")

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
            print("Reading message:......")
            message.Command = reader.ReadFixedString(12)
            print("command is :%s " % message.Command)


            somethingElse = reader.ReadUInt32()
            print("Something else: %s " % somethingElse)

            length = reader.ReadUInt32()
            print("LENGTH: %s " % length)
            if length > Message.PayloadMaxSizeInt:
                raise Exception("format too big")

            message.Checksum = reader.ReadUInt32()
            #1086745783
            #2198620797
            print("Checksum: %s " % message.Checksum)
            message.Payload = bytearray(length)

            if len(message.Payload) > 0:
                socket.recv_into(message.Payload)

            print("message payload is :%s " % message.Payload)
            checksum = Message.GetChecksum(message.Payload)

            if checksum != message.Checksum:
                raise Exception("invalid checksum")

            return message

        except Exception as e:
                print("could not receive buffer from socket: %s " % e)





    @staticmethod
    def FillBufferAsyncStream(stream, buffer, cancellation_token):
        raise NotImplementedError()

    @staticmethod
    async def FillBufferAsyncSocket(socket, buffer, cancellation_token):
        raise NotImplementedError()



    @staticmethod
    def GetChecksum(value):
#        if type(value) is bytearray:
#            print("do something here")
#            try:
#                value = value.decode('utf-8')
#            except UnicodeDecodeError as e:
#                print("could not decode as utf-8")
#                value = value.decode('latin-1')
#            except Exception as e:
#                print("Could not decode byte array: %s " % value)

        uint32 = bin_dbl_sha256(value)[:4]

        return int.from_bytes( uint32, 'little')



    def Serialize(self, writer):

        writer.WriteUInt32(self.Magic)
        writer.WriteFixedString(self.Command, 12)
        writer.WriteUInt32(len(self.Payload))
        writer.WriteUInt32(self.Checksum)
        writer.WriteBytes(self.Payload)

