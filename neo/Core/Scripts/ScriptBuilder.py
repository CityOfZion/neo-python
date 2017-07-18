# -*- coding:utf-8 -*-
"""
Description:
    ScriptBuilder in neo, to create scripts
Usage:
    from neo.Core.Scripts.ScriptBuilder import ScriptBuilder
"""

import binascii

from neo.Core.Scripts.ScriptOp import ScriptOp
from neo.IO.MemoryStream import MemoryStream

class ScriptBuilder(object):
    """docstring for ScriptBuilder"""
    def __init__(self):
        super(ScriptBuilder, self).__init__()
        self.ms = MemoryStream()  # MemoryStream

    def add(self, op):
        if isinstance(op, int):
            self.ms.write(chr(op))
        else:
            self.ms.write(op)
        return

    def push(self, data):
        if data == None:
            return
        if isinstance(data,int):
            if data == -1:
                return self.add(ScriptOp.PUSHM1)
            elif data == 0:
                return self.add(ScriptOp.PUSH0)
            elif data > 0 and data <= 16:
                return self.add(ScriptOp.PUSH1M1 + bytes(data))
            else:
                return self.push(bytes(data))
        else:
            buf = binascii.unhexlify(data)
            if len(buf) <= int.from_bytes(ScriptOp.PUSHBYTES75, byteorder='big'):
                self.add(bytes(len(buf)))
                self.add(buf)
            elif len(buf) < int.from_bytes(b'\x10\x00', byteorder='big'):
                self.add(ScriptOp.PUSHDATA1)
                self.add(bytes(len(buf)))
                self.add(buf)
            elif len(buf) < int.from_bytes(b'\x10\x00\x00', byteorder='big'):
                self.add(ScriptOp.PUSHDATA2)
                self.add(bytes(len(buf)) & 0xff)
                self.add(bytes(len(buf)) >> 8)
                self.add(buf)
            elif len(buf) < int.from_bytes(b'\x10\x00\x00\x00', byteorder='big'):
                self.add(ScriptOp.PUSHDATA4)
                self.add(bytes(len(buf)) & 0xff)
                self.add((bytes(len(buf)) >> 8) & 0xff)
                self.add((bytes(len(buf)) >> 16) & 0xff)
                self.add(bytes(len(buf)) >> 24)
                self.add(buf)
        return

    def toArray(self):
        return self.ms.toArray()


if __name__ == '__main__':
    from bitcoin import privkey_to_pubkey
    pubkey = privkey_to_pubkey('L1RrT1f4kXJGnF2hESU1AbaQQG82WqLsmWQWEPGm2fbrNLwdrAV9')
    sb = ScriptBuilder()
    sb.add(21)
    sb.push(pubkey)
    sb.add(ScriptOp.OP_CHECKSIG)
    print((sb.toArray()))
