# -*- coding:utf-8 -*-
"""
Description:
    Inventory Class
Usage:
    from AntShares.Network.Inventory import Inventory
"""


class Inventory(object):
    """docstring for Inventory"""
    def __init__(self, hash=None):
        super(Inventory, self).__init__()
        self.hash = hash

    def ensureHash(self):
        if self.hash:
            return self.hash

    def deserialize(self):
        pass

        
