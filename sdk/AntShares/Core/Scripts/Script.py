# -*- coding:utf-8 -*-
"""
Description:
    Script
Usage:
    from AntShares.Core.Scripts.Script import Script
"""


from AntShares.Core.Scripts.Script import ISerializable


class Script(ISerializable):
    """docstring for Script"""
    def __init__(self):
        super(Script, self).__init__()
        self.stackScript = None
        self.redeemScript = None

    def serialize(self, writer):
        writer.writeVarBytes(self.stackScript)
        writer.writeVarBytes(self.redeemScript)

    def deserialize(self, reader):
        pass
