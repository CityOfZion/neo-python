from .StateBase import StateBase
from neo.Core.Size import Size as s


class BlockState(StateBase):

    def __init__(self):
        self.SystemFeeAmount = 0
        self.TrimmedBlock = None

    def Size(self):
        super(BlockState, self).Size() + s.uint64 + self.SystemFeeAmount

    def Deserialize(self, reader):
        super(BlockState, self).Deserialize(reader)
        self.SystemFeeAmount = reader.BinaryReader.ReadInt64()
        # self.TrimmedBlock =
        raise NotImplementedError("TrimmedBlock not implemented")

    def Serialize(self, writer):
        raise NotImplementedError("TrimmedBlock not implemented")

    def ToJson(self):
        raise NotImplementedError("TrimmedBlock not implemented")

    def Clone(self):
        bs = BlockState()
        bs.SystemFeeAmount = self.SystemFeeAmount
        bs.TrimmedBlock = self.TrimmedBlock
        return bs
