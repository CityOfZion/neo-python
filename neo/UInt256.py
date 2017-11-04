from neo.UIntBase import UIntBase


class UInt256(UIntBase):
    def __init__(self, data=None):
        super(UInt256, self).__init__(num_bytes=32, data=data)
