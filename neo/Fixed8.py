# -*- coding:utf-8 -*-
"""
Description:
    Fixed8
Usage:
    from neo.Fixed8 import Fixed8
"""


from decimal import Decimal as D
from neo.Helper import big_or_little


class Fixed8:

    value = 0

    D = 100000000



    """docstring for Fixed8"""
    def __init__(self, number):
        self.value = number



    @staticmethod
    def FromDecimal(number):
        out = int(number * Fixed8.D)
        return Fixed8(out)

    @staticmethod
    def Satoshi():
        return Fixed8(1)

    @staticmethod
    def NegativeSatoshi():
        return Fixed8(-1)

    @staticmethod
    def Zero():
        return Fixed8(0)



    def __add__(self, other):
        return Fixed8( self.value + other.value)
    def __iadd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        return Fixed8( self.value - other.value)
    def __isub__(self, other):
        return self.__sub__(other)

    def __mul__(self, other):
        return Fixed8( self.value * other.value)
    def __imul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        return Fixed8( int(self.value / other.value))
    def __itruediv__(self, other):
        return self.__truediv__(other)

    def __mod__(self, other):
        return Fixed8( int(self.value % other.value))
    def __imod__(self, other):
        return self.__imod__(other)



    def __pow__(self, power, modulo=None):
        return Fixed8( pow(self.value, power.value, modulo))

    def __neg__(self):
        return Fixed8(-1 * self.value)