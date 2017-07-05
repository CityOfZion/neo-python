# -*- coding:utf-8 -*-
"""
Description:
    Transaction Output
Usage:
    from AntShares.Core.TransactionOutput import TransactionOutput
"""


from AntShares.IO.ISerializable import ISerializable
from AntShares.Helper import big_or_little
from AntShares.Fixed8 import Fixed8


class TransactionOutput(ISerializable):
    """docstring for TransactionOutput"""
    def __init__(self, AssetId, Value, ScriptHash):
        super(TransactionOutput, self).__init__()
        self.AssetId = AssetId
        self.Value = Fixed8(Value)
        self.ScriptHash = ScriptHash

    def serialize(self, writer):
        # Serialize
        writer.writeBytes(big_or_little(self.AssetId))
        writer.writeFixed8(self.Value)
        writer.writeBytes(self.ScriptHash)

    def deserialize(self, reader):
        # Deserialize
        pass
