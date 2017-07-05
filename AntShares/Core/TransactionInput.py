# -*- coding:utf-8 -*-
"""
Description:
    Transaction Input
Usage:
    from AntShares.Core.TransactionInput import TransactionInput
"""


from AntShares.IO.ISerializable import ISerializable
from AntShares.Helper import big_or_little


class TransactionInput(ISerializable):
    """docstring for TransactionInput"""
    def __init__(self, prevHash, prevIndex):
        super(TransactionInput, self).__init__()
        self.prevHash = prevHash
        self.prevIndex = int(prevIndex)

    def serialize(self, writer):
        # Serialize
        writer.writeBytes(big_or_little(self.prevHash))
        writer.writeUInt16(self.prevIndex)

    def deserialize(self, reader):
        # Deserialize
        pass

    def toString(self):
        # to string
        return bytes(self.prevHash) + ":" + bytes(self.prevIndex)
