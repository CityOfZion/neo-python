
from neo.Cryptography.Helper import base256_encode



class BigInteger(int):

    @staticmethod
    def FromBytes(data, signed=True):
        return BigInteger( int.from_bytes(data,'little',signed=signed))

    def Equals(self, other):
        return super(BigInteger, self).__eq__(other)

    def ToByteArray(self, signed=True):
        try:
            return self.to_bytes((self.bit_length() + 7) //8, byteorder='little', signed=signed)
        except OverflowError:
            return self.to_bytes((self.bit_length() + 7) //8, byteorder='little', signed=False)
        except Exception:
            print("COULD NOT CONVERT %s to byte array" % self)

    def __abs__(self, *args, **kwargs):  # real signature unknown
        return BigInteger(super(BigInteger, self).__abs__(*args, **kwargs))

    def __add__(self, *args, **kwargs):  # real signature unknown
        return BigInteger(super(BigInteger, self).__add__(*args, **kwargs))


    def __mod__(self, *args, **kwargs):  # real signature unknown
        return BigInteger(super(BigInteger, self).__mod__(*args, **kwargs))

    def __mul__(self, *args, **kwargs):  # real signature unknown
        return BigInteger(super(BigInteger, self).__mul__(*args, **kwargs))

    def __neg__(self, *args, **kwargs):  # real signature unknown
        return BigInteger(super(BigInteger, self).__neg__(*args, **kwargs))

    def __str__(self, *args, **kwargs):  # real signature unknown
        return super(BigInteger, self).__str__(*args, **kwargs)

    def __sub__(self, *args, **kwargs):  # real signature unknown
        return BigInteger(super(BigInteger, self).__sub__(*args, **kwargs))

    def __truediv__(self, *args, **kwargs):  # real signature unknown
        return BigInteger(int(super(BigInteger, self).__truediv__(*args, **kwargs)))



ZERO = BigInteger(0)
ONE = BigInteger(1)