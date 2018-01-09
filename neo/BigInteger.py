from logzero import logger

from neocore.Cryptography.Helper import base256_encode


class BigInteger(int):

    @property
    def Sign(self):
        if self > 0:
            return 1
        elif self == 0:
            return 0
        return -1

    @staticmethod
    def FromBytes(data, signed=False):
        return BigInteger(int.from_bytes(data, 'little', signed=signed))

    def Equals(self, other):
        return super(BigInteger, self).__eq__(other)

    def ToByteArray(self, signed=True):

        if self < 0:
            try:
                return self.to_bytes(1 + ((self.bit_length() + 7) // 8), byteorder='little', signed=True)
            except Exception as e:
                logger.error("Couldn't convert negative number %s " % e)
                return False
        try:
            return self.to_bytes((self.bit_length() + 7) // 8, byteorder='little', signed=signed)
        except OverflowError:
            return self.to_bytes(1 + ((self.bit_length() + 7) // 8), byteorder='little', signed=signed)
        except Exception:
            logger.error("COULD NOT CONVERT %s to byte array" % self)

        return bytearray([0])

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

    def __floordiv__(self, *args, **kwargs):
        return BigInteger(super(BigInteger, self).__floordiv__(*args, **kwargs))

    def __truediv__(self, *args, **kwargs):  # real signature unknown
        return BigInteger(super(BigInteger, self).__truediv__(*args, **kwargs))


ZERO = BigInteger(0)
ONE = BigInteger(1)
