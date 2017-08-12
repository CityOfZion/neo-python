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

class ScriptBuilder(object):
    """docstring for ScriptBuilder"""
    def __init__(self):
        super(ScriptBuilder, self).__init__()
        self.ms = MemoryStream()  # MemoryStream

    def add(self, op):
        if isinstance(op, int):
            self.ms.write(bytes([op]))
        else:
            self.ms.write(op)
        return

    def push(self, data):
        if data == None:
            return
        if isinstance(data,int):
            if data == -1:
                return self.add(PUSHM1)
            elif data == 0:
                return self.add(PUSH0)
            elif data > 0 and data <= 16:
                return self.add(int.from_bytes(PUSH1,'big') -1  + data)
            else:
                return self.push(bytes(data))
        else:
            buf = binascii.unhexlify(data)
        if len(buf) <= int.from_bytes( PUSHBYTES75, 'big'):
            self.add(len(buf))
            self.add(buf)
        elif len(buf) < 0x100:
            self.add(PUSH1)
            self.add(len(buf))
            self.add(buf)
        elif len(buf) < 0x10000:
            self.add(PUSH2)
            self.add(len(buf) & 0xff)
            self.add(len(buf) >> 8)
            self.add(buf)
        elif len(buf) < 0x100000000:
            self.add(PUSH4)
            self.add(len(buf) & 0xff)
            self.add((len(buf) >> 8) & 0xff)
            self.add((len(buf) >> 16) & 0xff)
            self.add(len(buf) >> 24)
            self.add(buf)
        return

    def ToArray(self):
        self.ms.flush()
        retval = self.ms.ToArray()
        self.ms.Cleanup()
        self.ms = None

        return retval


