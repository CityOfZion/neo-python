# -*- coding:utf-8 -*-
"""
Description:
    Basic class for Serialization
"""


class SerializableMixin(object):
    """ISerializable InterFace"""

    def Serialize(self, writer):
        pass

    def Deserialize(self, reader):
        pass

    def ToArray(self):
        pass


class TrackableMixin(object):

    Key = None
    TrackingState = None
