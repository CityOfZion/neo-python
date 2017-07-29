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
#        ba = self.ReadBytes(length)
#        print("BA UNPACK: %s " % ba)
        return struct.unpack(fmt, self.stream.read(length))[0]

    def ReadByte(self):
        return ord(self.stream.read(1))

    def ReadBytes(self, length):
        value = self.stream.read(length)
#        try:
#            return binascii.hexlify(value)
#        except:
        return value

    def ReadBool(self):
        return self.unpack('?')

    def ReadChar(self):
        return self.unpack('c')

    def ReadInt8(self):
        return self.unpack('b')

    def ReadUInt8(self):
        return self.unpack('B')


    def ReadInt16(self):
        return self.unpack('h', 2)

    def ReadUInt16(self):
#        print("reading 16")
#        val = self.stream.read(2)
#        print("val16: %s " % val)
#        intval = int.from_bytes(val, 'big', signed=False)
#        print("16 intval: %s " % intval)
#        return intval
        return self.unpack('H', 2)

    def ReadInt32(self):
        return self.unpack('i', 4)

    def ReadUInt32(self):
        print("reading uint 32111")
#        val = self.stream.read(4)
#        intval = int.from_bytes(val, 'big',signed=False)
#        print("stream val 32 %s "% val)
#        print("32 intval: %s " % intval)
#        return intval
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
        print("read var int value %s " % fb)
        if fb == b'\xfd':
            print("read 16!")
            value = self.ReadUInt16()
        elif fb == b'\xfe':
            print("read 32!!!")
            value = self.ReadUInt32()
        elif fb == b'\xff':
            print("read 64!")
            value = self.ReadUInt64()
        else:
            print("read default!!!!")
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
        print("var string length: %s " % length)

        return self.unpack(str(length) + 's', length)

    def ReadFixedString(self, length):
        return self.ReadBytes(length).rstrip(b'\x00')

    def ReadSerializableArray(self, class_name):

        module = '.'.join(class_name.split('.')[:-1])
        klassname = class_name.split('.')[-1]
        klass = getattr(importlib.import_module(module), klassname)
#
        length = self.ReadVarInt()

        items = []

        for i in range(0, length):
            item = klass()
            item.Deserialize(self)
            items.append(item)

        return items

