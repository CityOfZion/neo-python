# -*- coding:utf-8 -*-
"""
Description:
    Fixed8
Usage:
    from AntShares.Fixed8 import Fixed8
"""


from AntShares.Helper import big_or_little


class Fixed8(float):
    """docstring for Fixed8"""
    def __init__(self, number):
        super(Fixed8, self).__init__(number)
        self.f = float(number)
        self.base = 0x10000000000000000

    def getData(self):
        return big_or_little(hex(self.base + int(self.f/0.00000001))[-17:-1])
