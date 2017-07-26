# -*- coding:utf-8 -*-
"""
Description:
    Script
Usage:
    from neo.Core.Scripts.Script import Script
"""


from neo.IO.Mixins import SerializableMixin


class Script(ISerializable):
    """docstring for Script"""
    def __init__(self):
        super(Script, self).__init__()
        self.stackScript = None
        self.redeemScript = None

    def serialize(self, writer):
        writer.WriteVarBytes(self.stackScript)
        writer.WriteVarBytes(self.redeemScript)

    def deserialize(self, reader):
        pass
