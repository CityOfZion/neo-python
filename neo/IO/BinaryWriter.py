# -*- coding:utf-8 -*-
"""
Description:
    Binary Writer
Usage:
    from neo.IO.BinaryWriter import BinaryWriter
"""


import struct
import binascii


class BinaryWriter(object):
    """docstring for BinaryWriter"""
    def __init__(self, stream):
        super(BinaryWriter, self).__init__()
        self.stream = stream

    def WriteByte(self, value):
        if type(value) is bytes:
            print("writing bytes::::::::::")
            self.stream.write(chr(value))
        elif type(value) is str:
            print("writing stringeeeee")
            self.stream.write(value.enconde('utf-8'))
        elif type(value) is int:
            self.stream.write(bytes([value]))
        else:
            #raise Exception("Could not write byte for type: %s " % type(value))
            print("Colud not write byte for type: %s " % type(value))

    def WriteBytes(self, value):
        try:
            value = binascii.unhexlify(value)
        except TypeError:
            pass
        except binascii.Error:
            pass
        self.stream.write(value)

    def pack(self, fmt, data):
        byts = struct.pack(fmt, data)
        print("pack bytes: %s " % byts)
        return self.WriteBytes(struct.pack(fmt, data))

    def WriteChar(self, value):
        return self.pack('c', value)

    def WriteInt8(self, value):
        return self.pack('b', value)

    def WriteUInt8(self, value):
        return self.pack('B', value)

    def WriteBool(self, value):
        return self.pack('?', value)

    def WriteInt16(self, value):
        return self.pack('h', value)

    def WriteUInt16(self, value):
        return self.pack('H', value)

    def WriteInt32(self, value):
        return self.pack('i', value)

    def WriteUInt32(self, value):
        return self.pack('I', value)

    def WriteInt64(self, value):
        return self.pack('q', value)

    def WriteUInt64(self, value):
        return self.pack('Q', value)

    def WriteFloat(self, value):
        return self.pack('f', value)

    def WriteDouble(self, value):
        return self.pack('d', value)

    def WriteVarInt(self, value):
        if not isinstance(value ,int):
            raise TypeError('%s not int type.' % value)

        if value < 0:
            raise Exception('%d too small.' % value)

        elif value < 0xfd:
            print("writing var int single byte: %s " % value)
            return self.WriteByte(value)

        elif value <= 0xffff:
            print("writing var int single byte fffff: %s " % value)
            self.WriteByte(0xfd)
            return self.WriteUInt16(value)

        elif value <= 0xFFFFFFFF:
            print("writing var int single byte fffffffff: %s " % value)
            self.WriteByte(0xfd)
            return self.WriteUInt32(value)

        else:
            self.WriteByte(0xff)
            return self.WriteUInt64(value)

    def WriteVarBytes(self, value):
        length = len(binascii.unhexlify(value))
        self.WriteVarInt(length)
        return self.WriteBytes(value)

    def WriteVarString(self, value):
        out = bytearray(value.encode('utf-8'))
        print("write var string, out: %s " %out)
        length = len(out)
        print("var string length: %s " % length)
        self.WriteVarInt(length)
        return self.WriteBytes(value.encode('utf-8'))

    def WriteFixedString(self, value, length):
        towrite = value.encode('utf-8')
        print("Writing fixed: %s %s " % (towrite, length))
        slen = len(towrite)
        if len(value) > slen:
            raise Exception("string longer than fixed length: %s " % length)
        self.WriteBytes(towrite)
        diff = length - slen

        while diff > 0:
            self.WriteByte(0)
            diff -=1

    def WriteSerializableArray(self, array):
        self.WriteVarInt(len(array))
        for item in array:
            item.serialize(self)

    def WriteFixed8(self, value):
        return self.WriteBytes(value.getData())
