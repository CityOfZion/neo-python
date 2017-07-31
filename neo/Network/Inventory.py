# -*- coding:utf-8 -*-
"""
Description:
    Inventory Class
Usage:
    from neo.Network.Inventory import Inventory
"""

from neo.IO.MemoryStream import MemoryStream
from neo.IO.BinaryWriter import BinaryWriter

from neo.Cryptography.Helper import *
from neo.Helper import *
from bitcoin import *
import binascii


class Inventory(object):
    """docstring for Inventory"""
    def __init__(self):
        super(Inventory, self).__init__()
        self.hash = None

    def EnsureHash(self):
        self.hash = big_or_little(binascii.hexlify(
                        bin_dbl_sha256(binascii.unhexlify(self.GetHashData()))))
        return self.hash

    def GetHashData(self):
        ms = MemoryStream()
        w = BinaryWriter(ms)
        self.SerializeUnsigned(w)
        return ms.ToArray()

    def GetScriptHashesForVerifying(self):
        pass

    def Serialize(self, writer):
        pass

    def SerializeUnsigned(self, writer):
        pass

    def Deserialize(self, reader):
        pass

    def DeserializeUnsigned(self, reader):
        pass
