# -*- coding:utf-8 -*-
"""
Description:
    Transaction Output
Usage:
    from AntShares.Core.TransactionOutput import TransactionOutput
"""


from AntShares.IO.ISerializable import ISerializable


class TransactionOutput(ISerializable):
    """docstring for TransactionOutput"""
    def __init__(self, AssetId, Value, ScriptHash):
        super(TransactionOutput, self).__init__()
        self.AssetId = AssetId
        self.Value = Value
        self.ScriptHash = ScriptHash

    def serialize(self, writer):
        # Serialize
        writer.writeString(self.AssetId)
        writer.writeFloat(self.Value)
        writer.writeString(self.ScriptHash)

    def deserialize(self, reader):
        # Deserialize
        pass
