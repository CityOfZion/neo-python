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
        try:
            return ord(self.stream.read(1))
        except Exception as e:
            print("Could not read byte: %s" % e)
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
#        print("reading 16")
#        val = self.stream.read(2)
#        print("val16: %s " % val)
#        intval = int.from_bytes(val, 'big', signed=False)
#        print("16 intval: %s " % intval)
#        return intval
        return self.unpack('%sH' % endian, 2)

    def ReadInt32(self, endian="<"):
        return self.unpack('%si' % endian, 4)

    def ReadUInt32(self, endian="<"):
        print("reading uint 32111")
#        val = self.stream.read(4)
#        intval = int.from_bytes(val, 'big',signed=False)
#        print("stream val 32 %s "% val)
#        print("32 intval: %s " % intval)
#        return intval
        return self.unpack('%sI' % endian, 4)

    def ReadInt64(self, endian="<"):
        return self.unpack('%sq' % endian, 8)

    def ReadUInt64(self, endian="<"):
        return self.unpack('%sQ' % endian, 8)


    def ReadVarInt(self):
        fb = self.ReadByte()
        if fb is None: return 0
        value = 0
        print("read var int value %s " % hex(fb))
        if hex(fb) == '0xfd':
            print("read 16!")
            value = self.ReadUInt16()
        elif hex(fb) == '0xfe':
            print("read 32!!!")
            value = self.ReadUInt32()
        elif hex(fb) == '0xff':
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
        print("Reading serializable %s " % class_name)
        print("NUM Serializable %s " % length)
        items = []

        for i in range(0, length):
            item = klass()
            item.Deserialize(self)
            items.append(item)

        return items


    def ReadUInt256(self):
        ba = bytearray(self.ReadBytes(32))
        ba.reverse()
        return ba

    def ReadUInt160(self):
        return self.ReadBytes(20)

    def ReadHashes(self):
        len = self.ReadUInt8()
        items = []
        for i in range(0, len):
            items.append( self.ReadUInt256())

        return items