# -*- coding:utf-8 -*-
"""
Description:
    Binary Writer
Usage:
    from neo.IO.BinaryWriter import BinaryWriter
"""
import sys
import os
import inspect
import struct
import binascii

from logzero import logger

from neo.UInt160 import UInt160
from neo.UInt256 import UInt256


def swap32(i):
    return struct.unpack("<I", struct.pack(">I", i))[0]


def convert_to_uint160(value):
    return bin(value + 2**20)[-20:]


def convert_to_uint256(value):
    return bin(value + 2**32)[-32:]


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

    def WriteBytes(self, value, unhex=True):
        if unhex:
            try:
                value = binascii.unhexlify(value)
            except TypeError as t:
                pass
            except binascii.Error as be:
                pass

        self.stream.write(value)

    def pack(self, fmt, data):
        return self.WriteBytes(struct.pack(fmt, data), unhex=False)

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
        if type(value) is UInt160:
            value.Serialize(self)
        else:
            raise Exception("value must be UInt160 instance ")

    def WriteUInt256(self, value):
        if type(value) is UInt256:
            value.Serialize(self)
        else:
            raise Exception("Cannot write value that is not UInt256")
    #        return self.pack('%sQ' % endian, value)

    def WriteVarInt(self, value, endian="<"):
        if not isinstance(value, int):
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
        if type(value) is str:
            value = value.encode(encoding)

        length = len(value)
        ba = bytearray(value)
        byts = binascii.hexlify(ba)
        string = byts.decode(encoding)
        self.WriteVarInt(length)
        self.WriteBytes(string)

    def WriteFixedString(self, value, length):
        towrite = value.encode('utf-8')
        slen = len(towrite)
        if len(value) > slen:
            raise Exception("string longer than fixed length: %s " % length)
        self.WriteBytes(towrite)
        diff = length - slen

        while diff > 0:
            self.WriteByte(0)
            diff -= 1

    def WriteSerializableArray(self, array):
        if array is None:
            self.WriteByte(0)
        else:
            self.WriteVarInt(len(array))
            for item in array:
                item.Serialize(self)

    def Write2000256List(self, arr):
        for item in arr:
            ba = bytearray(binascii.unhexlify(item))
            ba.reverse()
            self.WriteBytes(ba)

    def WriteHashes(self, arr):
        length = len(arr)
        self.WriteVarInt(length)
        for item in arr:
            ba = bytearray(binascii.unhexlify(item))
            ba.reverse()
#            logger.info("WRITING HASH %s " % ba)
            self.WriteBytes(ba)

    def WriteFixed8(self, value, unsigned=False):
        #        if unsigned:
        #            return self.WriteUInt64(int(value.value))
        return self.WriteInt64(value.value)
