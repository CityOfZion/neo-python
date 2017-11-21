# -*- coding:utf-8 -*-
"""
Description:
    Fixed8
Usage:
    from neo.Fixed8 import Fixed8
"""


class Fixed8:

    value = 0

    D = 100000000

    """docstring for Fixed8"""

    def __init__(self, number):
        self.value = number

    def GetData(self):
        return self.value

    @staticmethod
    def FD():
        return Fixed8(Fixed8.D)

    @staticmethod
    def FromDecimal(number):
        out = int(number * Fixed8.D)
        return Fixed8(out)

    @staticmethod
    def Satoshi():
        return Fixed8(1)

    @staticmethod
    def One():
        return Fixed8(Fixed8.D)

    @staticmethod
    def NegativeSatoshi():
        return Fixed8(-1)

    @staticmethod
    def Zero():
        return Fixed8(0)

    @staticmethod
    def TryParse(value, require_positive=False):
        val = None
        try:
            val = float(value)
        except Exception as e:
            pass
        if not val:
            try:
                val = int(value)
            except Exception as e:
                pass
        if val:

            if require_positive and val < 0:
                return None

            return Fixed8(int(val * Fixed8.D))

        return None

    def __add__(self, other):
        return Fixed8(self.value + other.value)

    def __iadd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        return Fixed8(self.value - other.value)

    def __isub__(self, other):
        return self.__sub__(other)

    def __mul__(self, other):
        return Fixed8(self.value * other.value)

    def __imul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        return Fixed8(int(self.value / other.value))

    def __floordiv__(self, other):
        return Fixed8(self.value // other.value)

    def __itruediv__(self, other):
        return self.__truediv__(other)

    def __mod__(self, other):
        return Fixed8(int(self.value % other.value))

    def __imod__(self, other):
        return self.__imod__(other)

    def __pow__(self, power, modulo=None):
        return Fixed8(pow(self.value, power.value, modulo))

    def __neg__(self):
        return Fixed8(-1 * self.value)

    def __eq__(self, other):
        return self.value == other.value

    def __lt__(self, other):
        return self.value < other.value

    def __gt__(self, other):
        return self.value > other.value

    def __ge__(self, other):
        return self.value >= other.value

    def __le__(self, other):
        return self.value <= other.value

    def ToString(self):
        return self.value / Fixed8.D
#    def __str__(self):
#        return self.value
