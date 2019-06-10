from neo.Network.core.uintbase import UIntBase


class UInt256(UIntBase):
    def __init__(self, data=None):
        super(UInt256, self).__init__(num_bytes=32, data=data)

    @staticmethod
    def from_string(value):
        if value[0:2] == '0x':
            value = value[2:]
        if not len(value) == 64:
            raise ValueError(f"Invalid UInt256 Format: {len(value)} chars != 64 chars")
        reversed_data = bytearray.fromhex(value)
        reversed_data.reverse()
        return UInt256(data=reversed_data)

    @classmethod
    def zero(cls):
        return cls(data=bytearray(32))
