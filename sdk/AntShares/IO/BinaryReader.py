# -*- coding:utf-8 -*-
"""
Description:
    Binary Reader
Usage:
    from AntShares.IO.BinaryReader import BinaryReader
"""


import struct


class BinaryReader(object):
    """docstring for BinaryReader"""
    def __init__(self, stream):
        super(BinaryReader, self).__init__()
        self.stream = stream

    def readByte(self):
        return self.stream.read(1)

    def readBytes(self, length):
        return self.stream.read(length)

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

    def readString(self):
        length = self.readUInt16()
        return self.unpack(str(length) + 's', length)
