
from neo.Cryptography.Helper import base256_encode



class BigInteger(int):

    _value = None


    def __init__(self, value):
        self._value = value


    def ToByteArray(self):
        return base256_encode(self._value)


ZERO = BigInteger(0)
ONE = BigInteger(1)