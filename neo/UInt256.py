from neo.UIntBase import UIntBase

import binascii


class UInt256(UIntBase):
    def __init__(self, data=None):
        super(UInt256, self).__init__(num_bytes=32, data=data)

    def Serialize(self, writer):
        writer.WriteBytes(self.Data)

    def Deserialize(self, reader):
        self.Data = reader.ReadBytes(32)
