# -*- coding:utf-8 -*-
"""
Description:
    Binary Writer
Usage:
    from AntShares.IO.BinaryWriter import BinaryWriter
"""


import struct
import binascii


class BinaryWriter(object):
    """docstring for BinaryWriter"""
    def __init__(self, stream):
        super(BinaryWriter, self).__init__()
        self.stream = stream

    def writeByte(self, value):
        self.stream.write(chr(value))

    def writeBytes(self, value):
        try:
            value = binascii.unhexlify(value)
        except TypeError:
            pass
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

    def writeVarInt(self, value):
        if not isinstance(value ,int):
            raise TypeError, '%s not int type.' % value

        if value < 0:
            raise Exception, '%d too small.' % value

        elif value < 0xfd:
            return self.writeByte(value)

        elif value <= 0xffff:
            self.writeByte(0xfd)
            return self.writeUInt16(value)

        elif value <= 0xFFFFFFFF:
            self.writeByte(0xfd)
            return self.writeUInt32(value)

        else:
            self.writeByte(0xff)
            return self.writeUInt64(value)

    def writeVarBytes(self, value):
        length = len(binascii.unhexlify(value))
        self.writeVarInt(length)
        return self.writeBytes(value)

    def writeString(self, value):
        length = len(binascii.unhexlify(value))
        self.writeUInt8(length)
        return self.pack(str(length) + 's', value)

    def writeSerializableArray(self, array):
        self.writeVarInt(len(array))
        for item in array:
            item.serialize(self)

    def writeFixed8(self, value):
        return self.writeBytes(value.getData())
