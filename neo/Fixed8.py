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
        out = number * Fixed8.D
        return Fixed8(out)

    @staticmethod
    def Satoshi():
        return Fixed8(1)