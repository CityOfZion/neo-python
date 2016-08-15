# -*- coding:utf-8 -*-
"""
Description:
    Binary Writer
Usage:
    from AntShares.IO.BinaryWriter import BinaryWriter
"""


import struct


class BinaryWriter(object):
    """docstring for BinaryWriter"""
    def __init__(self, stream):
        super(BinaryWriter, self).__init__()
        self.stream = stream

    def writeByte(self, value):
        self.stream.write(chr(value))

    def writeBytes(self, value):
        self.stream.write(value)

    def pack(self, fmt, data):
        return self.writeBytes(struct.pack(fmt, data))

    def writeChar(self, value):
        return self.pack('c', value)

    def writeInt8(self, value):
        return self.pack('b', value)

    def writeUInt8(self, value):
        return self.pack('B', value)

    def writeBool(self, value):
        return self.pack('?', value)

    def writeInt16(self, value):
        return self.pack('h', value)

    def writeUInt16(self, value):
        return self.pack('H', value)

    def writeInt32(self, value):
        return self.pack('i', value)

    def writeUInt32(self, value):
        return self.pack('I', value)

    def writeInt64(self, value):
        return self.pack('q', value)

    def writeUInt64(self, value):
        return self.pack('Q', value)

    def writeFloat(self, value):
        return self.pack('f', value)

    def writeDouble(self, value):
        return self.pack('d', value)

    def writeString(self, value):
        length = len(value)
        self.writeUInt8(length)
        return self.pack(str(length) + 's', value)


if __name__ == '__main__':
    from MemoryStream import MemoryStream
    a = MemoryStream()
    b = BinaryWriter(a)
    b.writeByte(0x40)
    Name = '测试'
    b.writeString("[{{'lang':'zh-CN','name':'%s'}}]" % Name)
    print 'a -> ',
    print repr(a.toArray())
