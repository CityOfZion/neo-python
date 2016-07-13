# -*- coding:utf-8 -*-
"""
Description:
    ScriptBuilder in AntShares, to create redeem script
Usage:
    from AntShares.Core.Scripts.ScriptBuilder import ScriptBuilder as sb
"""

from AntShare.Core.Scripts.ScriptOp import ScriptOp


class ScriptBuilder(object):
    """docstring for ScriptBuilder"""
    def __init__(self):
        super(ScriptBuilder, self).__init__()
        self.ms = bytearray()  # MemoryStream

    def add(self, op):
        if type(op) == 'int':
            self.ms.append(op)
        else:
            self.ms.extend(op)
        return

    def push(self, data):
        if data == None:
            return
        if type(data) == 'int':
            if data == -1:
                return self.add(ScriptOp.OP_1NEGATE)
            elif data == 0:
                return self.add(ScriptOp.OP_0)
            elif data > 0 and data <= 16:
                return self.add(ScriptOp.OP_1 - 1 + data)
            else:
                return self.push(bytearray([data]))
        else:
            buf = data
            if len(buf) <= ScriptOp.OP_PUSHBYTES75:
                self.add(buf.length())
                self.add(buf)
            elif len(buf) < 0x100:
                self.add(ScriptOp.OP_PUSHDATA1)
                self.add(buf.length())
                self.add(buf)
            elif len(buf) < 0x10000:
                self.add(ScriptOp.OP_PUSHDATA2)
                self.add(buf.length() & 0xff)
                self.add(buf.length() >> 8)
                self.add(buf)
            elif len(buf) < 0x100000000:
                self.add(ScriptOp.OP_PUSHDATA4)
                self.add(buf.length() & 0xff)
                self.add((buf.length() >> 8) & 0xff)
                self.add((buf.length() >> 16) & 0xff)
                self.add(buf.length() >> 24)
                self.add(buf)
        return

    def toArrary(self):
        return bytes(self.ms)
