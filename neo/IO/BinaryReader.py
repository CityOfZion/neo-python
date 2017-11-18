"""
Description:
    Binary Reader
Usage:
    from neo.IO.BinaryReader import BinaryReader
"""
import sys
import struct
import binascii
import importlib

from logzero import logger

from neo.Fixed8 import Fixed8
from neo.UInt160 import UInt160
from neo.UInt256 import UInt256


class BinaryReader(object):
    """docstring for BinaryReader"""

    def __init__(self, stream):
        super(BinaryReader, self).__init__()
        self.stream = stream

    def unpack(self, fmt, length=1):
        return struct.unpack(fmt, self.stream.read(length))[0]

    def ReadByte(self, do_ord=True):
        try:
            if do_ord:
                return ord(self.stream.read(1))
            return self.stream.read(1)
        except Exception as e:
            logger.error("ord expected character but got none")
        return 0

    def ReadBytes(self, length):
        value = self.stream.read(length)
        return value

    def ReadBool(self):
        return self.unpack('?')

    def ReadChar(self):
        return self.unpack('c')

    def ReadFloat(self, endian="<"):
        return self.unpack("%sf" % endian, 4)

    def ReadDouble(self, endian="<"):
        return self.unpack("%sd" % endian, 8)

    def ReadInt8(self, endian="<"):
        return self.unpack('%sb' % endian)

    def ReadUInt8(self, endian="<"):
        return self.unpack('%sB' % endian)

    def ReadInt16(self, endian="<"):
        return self.unpack('%sh' % endian, 2)

    def ReadUInt16(self, endian="<"):
        return self.unpack('%sH' % endian, 2)

    def ReadInt32(self, endian="<"):
        return self.unpack('%si' % endian, 4)

    def ReadUInt32(self, endian="<"):
        return self.unpack('%sI' % endian, 4)

    def ReadInt64(self, endian="<"):
        return self.unpack('%sq' % endian, 8)

    def ReadUInt64(self, endian="<"):
        return self.unpack('%sQ' % endian, 8)

    def ReadVarInt(self, max=sys.maxsize):
        fb = self.ReadByte()
        if fb is None:
            return 0
        value = 0
        if hex(fb) == '0xfd':
            value = self.ReadUInt16()
        elif hex(fb) == '0xfe':
            value = self.ReadUInt32()
        elif hex(fb) == '0xff':
            value = self.ReadUInt64()
        else:
            value = fb

        if value > max:
            raise Exception("Invalid format")

        return int(value)

    def ReadVarBytes(self, max=sys.maxsize):
        length = self.ReadVarInt(max)
        return self.ReadBytes(length)

    def ReadString(self):
        length = self.ReadUInt8()
        return self.unpack(str(length) + 's', length)

    def ReadVarString(self, max=sys.maxsize):
        length = self.ReadVarInt(max)
        return self.unpack(str(length) + 's', length)

    def ReadFixedString(self, length):
        return self.ReadBytes(length).rstrip(b'\x00')

    def ReadSerializableArray(self, class_name, max=sys.maxsize):

        module = '.'.join(class_name.split('.')[:-1])
        klassname = class_name.split('.')[-1]
        klass = getattr(importlib.import_module(module), klassname)
        length = self.ReadVarInt(max=max)
        items = []
#        logger.info("READING ITEM %s %s " % (length, class_name))
        try:
            for i in range(0, length):
                item = klass()
                item.Deserialize(self)
#                logger.info("deserialized item %s %s " % ( i, item))
                items.append(item)
        except Exception as e:
            logger.error("Couldn't deserialize %s " % e)

        return items

    def ReadUInt256(self):
        return UInt256(data=bytearray(self.ReadBytes(32)))

    def ReadUInt160(self):

        return UInt160(data=bytearray(self.ReadBytes(20)))

    def Read2000256List(self):
        items = []
        for i in range(0, 2000):
            data = self.ReadBytes(64)
            ba = bytearray(binascii.unhexlify(data))
            ba.reverse()
            items.append(ba.hex().encode('utf-8'))
        return items

    def ReadHashes(self, maximum=16):
        len = self.ReadVarInt()
        items = []
        for i in range(0, len):
            ba = bytearray(self.ReadBytes(32))
            ba.reverse()
            items.append(ba.hex())
        return items

    def ReadFixed8(self, unsigned=False):

        fval = self.ReadInt64()

        return Fixed8(fval)
