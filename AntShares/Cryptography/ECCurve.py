# -*- coding:utf-8 -*-
"""
Description:
    ECC Curve
Usage:
    from AntShares.Cryptography.ECCurve import ECCurve
"""


class ECCurveNotFound(Exception):
    """docstring for ECCurveNotFound"""
    def __init__(self, curve):
        super(ECCurveNotFound, self).__init__()
        self.curve = curve
    def __str__(self):
        return "ECC Curve '%s' cannot found." % self.curve


class ECCurve(object):
    """docstring for ECCurve"""
    def __init__(self, curve='secp256r1'):
        super(ECCurve, self).__init__()
        self.curve = curve
        self.get_curve()

    def secp256r1(self):
        self.P = int("FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF", 16)
        self.N = int("FFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551", 16)
        self.A = int("FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC", 16)
        self.B = int("5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B", 16)
        self.Gx = int("6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296", 16)
        self.Gy = int("4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5", 16)
        self.G = (self.Gx, self.Gy)

    def secp256k1(self):
        self.P = int("FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F", 16)
        self.N = int("FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC", 16)
        self.A = 0
        self.B = 7
        self.Gx = int("6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296", 16)
        self.Gy = int("4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5", 16)
        self.G = (self.Gx, self.Gy)

    def get_curve(self):
        try:
            func = self.__getattribute__(self.curve)
            func()
        except AttributeError as e:
            raise ECCurveNotFound(self.curve)
