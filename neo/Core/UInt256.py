from neo.Core.UIntBase import UIntBase


class UInt256(UIntBase):
    def __init__(self, data=None):
        super(UInt256, self).__init__(num_bytes=32, data=data)

    @staticmethod
    def ParseString(value):
        """
        Parse the input str `value` into UInt256

        Raises:
            ValueError: if the input `value` length (after '0x' if present) != 64
        """
        if value[0:2] == '0x':
            value = value[2:]
        if not len(value) == 64:
            raise ValueError(f"Invalid UInt256 input: {len(value)} chars != 64 chars")
        reversed_data = bytearray.fromhex(value)
        reversed_data.reverse()
        return UInt256(data=reversed_data)
