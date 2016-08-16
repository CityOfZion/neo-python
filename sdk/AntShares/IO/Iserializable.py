# -*- coding:utf-8 -*-
"""
Description:
    Basic class for Serialization
Usage:
    from AntShares.IO.ISerializable import ISerializable
"""


class ISerializable(object):
    """ISerializable InterFace"""
    def __init__(self):
        super(ISerializable, self).__init__()

    def Serialize(self, writer):
        pass

    def Deserialize(self, reader):
        pass
