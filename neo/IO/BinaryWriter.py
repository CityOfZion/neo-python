# -*- coding:utf-8 -*-
"""
Description:
    Binary Writer
Usage:
    from neo.IO.BinaryWriter import BinaryWriter
"""


import struct
import binascii
from autologging import logged

def swap32(i):
    return struct.unpack("<I", struct.pack(">I", i))[0]

def convert_to_uint160(value):
    return bin(value+2**20)[-20:]

def convert_to_uint256(value):
    return bin(value+2**32)[-32:]

@logged
class BinaryWriter(object):
    """docstring for BinaryWriter"""
    def __init__(self, stream):
        super(BinaryWriter, self).__init__()
        self.stream = stream

    def WriteByte(self, value):
        if type(value) is bytes:
            self.stream.write(value)
        elif type(value) is str:
            self.stream.write(value.enconde('utf-8'))
        elif type(value) is int:
            self.stream.write(bytes([value]))

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
        return self.WriteBytes(struct.pack(fmt, data))

    def WriteChar(self, value, endian="<"):
        return self.pack('c', value)

    def WriteFloat(self, value, endian="<"):
        return self.pack('%sf' % endian, value)

    def WriteDouble(self, value, endian="<"):
        return self.pack('%sd' % endian, value)

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

    def WriteUInt160(self, value, endian="<"):
        if type(value) is int:
            value = convert_to_uint160(value)
        return self.WriteBytes(value)

    def WriteUInt256(self, value, endian="<", destination_hash=True):
        if type(value) is int:
            value = convert_to_uint256(value)
        elif type(value) is bytearray:
            return self.WriteBytes(value)

        if destination_hash:
            ba = bytearray(binascii.unhexlify(value))
            ba.reverse()
            return self.WriteBytes(ba)

        return self.WriteBytes(value)
#        return self.pack('%sQ' % endian, value)


    def WriteVarInt(self, value, endian="<"):
        if not isinstance(value ,int):
            raise TypeError('%s not int type.' % value)

        if value < 0:
            raise Exception('%d too small.' % value)

        elif value < 0xfd:
            return self.WriteByte(value)

        elif value <= 0xffff:
            self.WriteByte(0xfd)
            return self.WriteUInt16(value, endian)

        elif value <= 0xFFFFFFFF:
            self.WriteByte(0xfd)
            return self.WriteUInt32(value, endian)

        else:
            self.WriteByte(0xff)
            return self.WriteUInt64(value, endian)

    def WriteVarBytes(self, value, endian="<", unhexlify=True):
        length = len(value)
        self.WriteVarInt(length, endian)
        return self.WriteBytes(value)

    def WriteVarString(self, value, endian="<", encoding="utf-8"):
        out = bytearray(value.encode(encoding))
        length = len(out)
        self.WriteVarInt(length, endian)
        return self.WriteBytes(value.encode('utf-8'))

    def WriteFixedString(self, value, length):
        towrite = value.encode('utf-8')
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
            item.Serialize(self)

    def Write2000256List(self, arr):
        for item in arr:
            self.WriteUInt256(item, "<",True)

    def WriteHashes(self, arr):
        length = len(arr)
        self.WriteUInt8(length)
        for item in arr:
            ba = bytearray(binascii.unhexlify(item))
            ba.reverse()
            self.WriteUInt256(ba,"<",False)


    def WriteFixed8(self, value):
        return self.WriteBytes(value.value)
