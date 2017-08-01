# -*- coding:utf-8 -*-
"""
Description:
    Binary Reader
Usage:
    from neo.IO.BinaryReader import BinaryReader
"""


import struct
import binascii
import importlib
from autologging import logged


@logged
class BinaryReader(object):
    """docstring for BinaryReader"""
    def __init__(self, stream):
        super(BinaryReader, self).__init__()
        self.stream = stream


    def unpack(self, fmt, length=1):
        return struct.unpack(fmt, self.stream.read(length))[0]

    def ReadByte(self):
        return ord(self.stream.read(1))

    def ReadBytes(self, length):
        value = self.stream.read(length)
        return value

    def ReadBool(self):
        return self.unpack('?')

    def ReadChar(self):
        return self.unpack('c')

    def ReadFloat(self, endian="<"):
        return self.unpack("%sf" % endian)

    def ReadDouble(self, endian="<"):
        return self.unpack("%sd" % endian)

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


    def ReadVarInt(self):
        fb = self.ReadByte()
        if fb is None: return 0
        value = 0
        self.__log.debug("read var int value %s " % hex(fb))
        if hex(fb) == '0xfd':
            value = self.ReadUInt16()
        elif hex(fb) == '0xfe':
            value = self.ReadUInt32()
        elif hex(fb) == '0xff':
            value = self.ReadUInt64()
        else:
            value = fb
        return int(value)

    def ReadVarBytes(self):
        length = self.ReadVarInt()
        return self.ReadBytes(length)

    def ReadString(self):
        length = self.ReadUInt8()
        return self.unpack(str(length) + 's', length)

    def ReadVarString(self):
        length = self.ReadVarInt()
        return self.unpack(str(length) + 's', length)

    def ReadFixedString(self, length):
        return self.ReadBytes(length).rstrip(b'\x00')

    def ReadSerializableArray(self, class_name):

        module = '.'.join(class_name.split('.')[:-1])
        klassname = class_name.split('.')[-1]
        klass = getattr(importlib.import_module(module), klassname)
        length = self.ReadVarInt()
        items = []

        for i in range(0, length):
            item = klass()
            item.Deserialize(self)
            items.append(item)

        return items


    def ReadUInt256(self, reverse = True):
        ba = bytearray(self.ReadBytes(32))
        if reverse:
            ba.reverse()
        return ba

    def ReadUInt160(self, reverse=False, hex=False):
        ba = bytearray(self.ReadBytes(20))
        if reverse:
            ba.reverse()
        if hex:
            return binascii.hexlify(ba)

        return ba

    def ReadHashes(self):
        len = self.ReadUInt8()
        items = []
        for i in range(0, len):
            items.append( (self.ReadUInt256().hex()))
        return items