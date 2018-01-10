# -*- coding:utf-8 -*-
"""
Description:
    ScriptBuilder in neo, to create scripts
Usage:
    from neo.Core.Scripts.ScriptBuilder import ScriptBuilder
"""

import binascii

from neo.VM.OpCode import *
from neo.IO.MemoryStream import MemoryStream
from neocore.Cryptography.Helper import base256_encode
from neocore.BigInteger import BigInteger
import struct


class ScriptBuilder(object):
    """docstring for ScriptBuilder"""

    def __init__(self):
        super(ScriptBuilder, self).__init__()
        self.ms = MemoryStream()  # MemoryStream

    def WriteUInt16(self, value, endian="<"):
        return self.pack('%sH' % endian, value)

    def WriteUInt32(self, value, endian="<"):
        return self.pack('%sI' % endian, value)

    def WriteUInt64(self, value, endian="<"):
        return self.pack('%sQ' % endian, value)

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
            self.WriteByte(0xfe)
            return self.WriteUInt32(value, endian)

        else:
            self.WriteByte(0xff)
            return self.WriteUInt64(value, endian)

    def WriteVarBytes(self, value, endian="<", unhexlify=True):
        length = len(value)
        self.WriteVarInt(length, endian)
        return self.WriteBytes(value)

    def WriteByte(self, value):
        if type(value) is bytes:
            self.ms.write(value)
        elif type(value) is str:
            self.ms.write(value.encode('utf-8'))
        elif type(value) is int:
            self.ms.write(bytes([value]))

    def WriteBytes(self, value):
        try:
            value = binascii.unhexlify(value)
        except TypeError:
            pass
        except binascii.Error:
            pass
        self.ms.write(value)

    def WriteBool(self, value, endian="<"):
        if value:
            self.add(PUSHT)
        else:
            self.add(PUSHF)

    def pack(self, fmt, data):
        return self.WriteBytes(struct.pack(fmt, data))

    def add(self, op):
        if isinstance(op, int):
            self.ms.write(bytes([op]))
        else:
            self.ms.write(op)
        return

    def push(self, data):
        if data is None:
            return

        if type(data) is bool:
            return self.add(data)

        if type(data) is int or type(data) is BigInteger:
            if data == -1:
                return self.add(PUSHM1)
            elif data == 0:
                return self.add(PUSH0)
            elif data > 0 and data <= 16:
                return self.add(int.from_bytes(PUSH1, 'little') - 1 + data)
            else:
                return self.push(binascii.hexlify(data.ToByteArray()))
        else:
            if not type(data) == bytearray:
                buf = binascii.unhexlify(data)
            else:
                buf = bytes(data)
        if len(buf) <= int.from_bytes(PUSHBYTES75, 'big'):
            self.add(len(buf))
            self.add(buf)
        elif len(buf) < 0x100:
            self.add(PUSHDATA1)
            self.add(len(buf))
            self.add(buf)
        elif len(buf) < 0x10000:
            self.add(PUSHDATA2)
            self.add(len(buf) & 0xff)
            self.add(len(buf) >> 8)
            self.add(buf)
        elif len(buf) < 0x100000000:
            self.add(PUSHDATA4)
            self.add(len(buf) & 0xff)
            self.add((len(buf) >> 8) & 0xff)
            self.add((len(buf) >> 16) & 0xff)
            self.add(len(buf) >> 24)
            self.add(buf)
        return

    def WriteVarData(self, data):
        length = len(data)

        if length <= 75:
            self.WriteByte(length)
        elif length < 0x100:
            self.ms.write(PUSHDATA1)
            self.WriteByte(length)
        elif length < 0x1000:
            self.ms.write(PUSHDATA2)
            self.WriteBytes(length.to_bytes(2, 'little'))
        elif length < 0x10000:
            self.ms.write(PUSHDATA4)
            self.WriteBytes(length.to_bytes(4, 'little'))

        self.WriteBytes(data)

    def Emit(self, op, arg=None):
        self.ms.write(op)
        if arg is not None:
            self.ms.write(arg)

    def EmitPushBigInteger(self, number):
        if number == -1:
            return self.Emit(PUSHM1)
        if number == 0:
            return self.Emit(PUSH0)
        if number > 0 and number <= 16:
            return self.Emit(int.from_bytes(PUSH1, 'little') - 1 + number)
        return self.Emit(number)

    def EmitAppCall(self, scriptHash, useTailCall=False):
        if len(scriptHash) != 20:
            raise Exception("Invalid script")
        if useTailCall:
            return self.Emit(TAILCALL, scriptHash)
        return self.Emit(APPCALL, scriptHash)

    def EmitAppCallWithOperationAndData(self, script_hash, operation, data):
        self.push(data)
        self.push(operation.encode('utf-8').hex())
        self.Emit(APPCALL, script_hash.Data)

    def EmitAppCallWithOperationAndArgs(self, script_hash, operation, args):
        args.reverse()
        for i in args:
            self.push(i)
        self.push(len(args))
        self.Emit(PACK)
        self.push(operation.encode('utf-8').hex())
        self.Emit(APPCALL, script_hash.Data)

    def EmitAppCallWithOperation(self, script_hash, operation):
        self.push(False)
        self.push(operation.encode('utf-8').hex())
        self.Emit(APPCALL, script_hash.Data)

    def EmitSysCall(self, api):
        if api is None:
            raise Exception("Please specify an api")

        api_bytes = bytearray(api.encode('utf-8'))
        length = len(api_bytes)
        length_bytes = bytearray(length.to_bytes(1, 'little'))
        out = length_bytes + api_bytes
        return self.Emit(SYSCALL, out)

    def EmitSysCallWithArguments(self, api, args):

        args.reverse()
        for argument in args:

            if type(argument) is bool:
                self.WriteBool(argument)
            elif type(argument) is bytes and len(argument) == 1:
                self.WriteByte(argument)
            else:
                self.push(binascii.hexlify(argument))

        self.EmitSysCall(api)

    def ToArray(self, cleanup=True):
        retval = self.ms.ToArray()
        if cleanup:
            self.ms.Cleanup()
            self.ms = None

        return retval
