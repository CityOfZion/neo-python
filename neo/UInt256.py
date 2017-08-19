from neo.UIntBase import UIntBase

import binascii

class UInt256(UIntBase):



    def __init__(self, data=None):

        super(UInt256, self).__init__(num_bytes=32, data=data)



    def Serialize(self, writer):

#        print("SERAILIZING UINT256: %s %s" % (self.ToBytes(), len(self.Data)))
        writer.WriteBytes(self.Data)

    def Deserialize(self, reader):
#        print("deserializing: %s %s" % (type(self),self.Size))
        self.Data = reader.ReadBytes(32)
#        print("deserialized UINT 256 %s " % self.Data)

