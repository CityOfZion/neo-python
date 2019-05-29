from neo.Network.core.uintbase import UIntBase


class UInt160(UIntBase):
    def __init__(self, data=None):
        super(UInt160, self).__init__(num_bytes=20, data=data)

    @staticmethod
    def from_string(value):
        if value[0:2] == '0x':
            value = value[2:]
        if not len(value) == 40:
            raise ValueError(f"Invalid UInt160 Format: {len(value)} chars != 40 chars")
        reversed_data = bytearray.fromhex(value)
        reversed_data.reverse()
        return UInt160(data=reversed_data)

    @classmethod
    def zero(cls):
        return cls(data=bytearray(20))
