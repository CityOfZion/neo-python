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

    def WriteChar(self, value, endian="<"):
        return self.pack('c', value)

    def WriteInt8(self, value, endian="<"):
        return self.pack('%sb' % endian, value)

    def WriteUInt8(self, value, endian="<"):
        return self.pack('%sB' % endian, value)

    def WriteBool(self, value, endian="<"):
        return self.pack('?', value)

    def WriteInt16(self, value, endian="<"):
        return self.pack('%sh' % endian, value)

    def WriteUInt16(self, value, endian="<"):
        return self.pack('%sH' % endian, value)

    def WriteInt32(self, value, endian="<"):
        return self.pack('%si' % endian, value)

    def WriteUInt32(self, value, endian="<"):
        return self.pack('%sI' % endian, value)

    def WriteInt64(self, value, endian="<"):
        return self.pack('%sq' % endian, value)

    def WriteUInt64(self, value, endian="<"):
        return self.pack('%sQ' % endian, value)

    def WriteFloat(self, value, endian="<"):
        return self.pack('%sf' % endian, value)

    def WriteDouble(self, value, endian="<"):
        return self.pack('%sd' % endian, value)

    def WriteVarInt(self, value, endian="<"):
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
            return self.WriteUInt16(value, endian)

        elif value <= 0xFFFFFFFF:
            print("writing var int single byte fffffffff: %s " % value)
            self.WriteByte(0xfd)
            return self.WriteUInt32(value, endian)

        else:
            self.WriteByte(0xff)
            return self.WriteUInt64(value, endian)

    def WriteVarBytes(self, value, endian="<"):
        length = len(binascii.unhexlify(value))
        self.WriteVarInt(length, endian)
        return self.WriteBytes(value)

    def WriteVarString(self, value, endian="<"):
        out = bytearray(value.encode('utf-8'))
        print("write var string, out: %s " %out)
        length = len(out)
        print("var string length: %s " % length)
        self.WriteVarInt(length, endian)
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
