# -*- coding:utf-8 -*-
"""
Description:
    Transaction Input
Usage:
    from AntShares.Core.TransactionInput import TransactionInput
"""


from AntShares.IO.ISerializable import ISerializable


class TransactionInput(ISerializable):
    """docstring for TransactionInput"""
    def __init__(self, prevHash, prevIndex):
        super(TransactionInput, self).__init__()
        self.prevHash = prevHash
        self.prevIndex = prevIndex

    def serialize(self, writer):
        # Serialize
        writer.writeBytes(self.prevHash)
        writer.writeUInt16(self.ScriptHash)

    def deserialize(self, reader):
        # Deserialize
        pass

    def toString(self):
        # to string
        return bytes(self.prevHash) + ":" + bytes(self.prevIndex)
