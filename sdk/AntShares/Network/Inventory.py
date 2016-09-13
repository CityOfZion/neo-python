# -*- coding:utf-8 -*-
"""
Description:
    Inventory Class
Usage:
    from AntShares.Network.Inventory import Inventory
"""

from AntShares.IO.MemoryStream import MemoryStream
from AntShares.IO.BinaryWriter import BinaryWriter

from AntShares.Cryptography.Helper import *
from AntShares.Helper import *

import binascii


class Inventory(object):
    """docstring for Inventory"""
    def __init__(self):
        super(Inventory, self).__init__()
        self.hash = None

    def ensureHash(self):
        self.hash = big_or_little(binascii.hexlify(
                        bin_dbl_sha256(binascii.unhexlify(self.getHashData()))))
        return self.hash

    def getHashData(self):
        ms = MemoryStream()
        w = BinaryWriter(ms)
        self.serializeUnsigned(w)
        return ms.toArray()

    def getScriptHashesForVerifying(self):
        pass

    def serialize(self):
        pass

    def serializeUnsigned(self):
        pass

    def deserialize(self):
        pass

    def deserializeUnsigned(self):
        pass
