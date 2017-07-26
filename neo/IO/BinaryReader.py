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

class BinaryReader(object):
    """docstring for BinaryReader"""
    def __init__(self, stream):
        super(BinaryReader, self).__init__()
        self.stream = stream


    def unpack(self, fmt, length=1):
        return struct.unpack(fmt, self.readBytes(length=length))[0]

    def ReadByte(self):
        return ord(self.stream.read(1))

    def ReadBytes(self, length):
        value = self.stream.read(length)
        try:
            return binascii.hexlify(value)
        except:
            return value

    def ReadChar(self):
        return self.unpack('c')

    def ReadInt8(self):
        return self.unpack('b')

    def ReadUInt8(self):
        return self.unpack('B')

    def ReadBool(self):
        return self.unpack('?')

    def ReadInt16(self):
        return self.unpack('h', 2)

    def ReadUInt16(self):
        return self.unpack('H', 2)

    def ReadInt32(self):
        return self.unpack('i', 4)

    def ReadUInt32(self):
        return self.unpack('I', 4)

    def ReadInt64(self):
        return self.unpack('q', 8)

    def ReadUInt64(self):
        return self.unpack('Q', 8)

    def ReadFloat(self):
        return self.unpack('f', 4)

    def ReadDouble(self):
        return self.unpack('d', 8)

    def ReadVarInt(self):
        fb = self.ReadByte()
        value = 0
        if fb == 0xfd:
            value = self.ReadUInt16()
        elif fb == 0xfe:
            value = self.ReadUInt32()
        elif fb == 0xff:
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

    def ReadFixedString(self, length):
        return self.ReadBytes(length).decode()

    def ReadSerializableArray(self, class_name):

        module = '.'.join(class_name.split('.')[:-1])
        klassname = class_name.split('.')[-1]
        klass = getattr(importlib.import_module(module), klassname)
        serializable = klass()

        length = self.ReadVarInt()

        items = []

        for i in range(0, length):
            item = klass()
            item.Deserialize(self)
            items.append(item)

        return items

        raise NotImplementedError()
