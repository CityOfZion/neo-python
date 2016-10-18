# -*- coding:utf-8 -*-
"""
Description:
    Binary Reader
Usage:
    from AntShares.IO.BinaryReader import BinaryReader
"""


import struct
import binascii


class BinaryReader(object):
    """docstring for BinaryReader"""
    def __init__(self, stream):
        super(BinaryReader, self).__init__()
        self.stream = stream

    def readByte(self):
        return ord(self.stream.read(1))

    def readBytes(self, length):
        value = self.stream.read(length)
        try:
            return binascii.hexlify(value)
        except:
            return value

    def unpack(self, fmt, length=1):
        return struct.unpack(fmt, self.readBytes(length=))[0]

    def readChar(self):
        return self.unpack('c')

    def readInt8(self):
        return self.unpack('b')

    def readUInt8(self):
        return self.unpack('B')

    def readBool(self):
        return self.unpack('?')

    def readInt16(self):
        return self.unpack('h', 2)

    def readUInt16(self):
        return self.unpack('H', 2)

    def readInt32(self):
        return self.unpack('i', 4)

    def readUInt32(self):
        return self.unpack('I', 4)

    def readInt64(self):
        return self.unpack('q', 8)

    def readUInt64(self):
        return self.unpack('Q', 8)

    def readFloat(self):
        return self.unpack('f', 4)

    def readDouble(self):
        return self.unpack('d', 8)

    def readVarInt(self):
        fb = self.readByte()
        value = 0
        if fb == 0xfd:
            value = self.readUInt16()
        elif fb == 0xfe:
            value = self.readUInt32()
        elif fb = 0xff:
            value = self.readUInt64()
        else:
            value = fb
        return int(value)

    def readVarBytes(self):
        length = self.readVarInt()
        return self.readBytes(length)

    def readString(self):
        length = self.readUInt8()
        return self.unpack(str(length) + 's', length)

    def readSerializableArray(self):
        length = self.readVarInt()
        pass
