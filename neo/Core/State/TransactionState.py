from .StateBase import StateBase
from neo.Core.Size import Size as s
from neo.Core.TX.Transaction import Transaction


class TransactionState(StateBase):

    def __init__(self, BlockIndex, tx):
        self.BlockIndex = BlockIndex
        self.Transaction = tx

    def Size(self):
        super(TransactionState, self).Size() + s.uint32 + self.Transaction.Size

    def Deserialize(self, reader):
        super(TransactionState, self).Deserialize(reader)
        self.BlockIndex = reader.ReadUInt32()
        self.Transaction = Transaction.DeserializeFrom(reader)

    def Serialize(self, writer):
        super(TransactionState, self).Serialize(writer)
        writer.WriteUInt32(self.BlockIndex)
        self.Transaction.Serialize(writer)

    def ToJson(self):
        json = super(TransactionState, self).ToJson()
        json['height'] = self.BlockIndex
        json['tx'] = self.Transaction.ToJson()
        return json

    def Clone(self):
        return TransactionState(self.BlockIndex, self.Transaction)
