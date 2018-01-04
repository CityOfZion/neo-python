# -*- coding:utf-8 -*-
"""
Description:
    Inventory Class
Usage:
    from neo.Network.Inventory import Inventory
"""

from neo.IO.MemoryStream import MemoryStream
from neocore.IO.BinaryWriter import BinaryWriter


class Inventory(object):
    """docstring for Inventory"""

    def __init__(self):
        """
        Create an instance
        """
        super(Inventory, self).__init__()
        self.hash = None

    def GetHashData(self):
        """
        Get the hashable data.

        Returns:
            bytes:
        """
        ms = MemoryStream()
        w = BinaryWriter(ms)
        self.SerializeUnsigned(w)
        ms.flush()
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
