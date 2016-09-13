# -*- coding:utf-8 -*-
"""
Description:
    MemoryStream
Usage:
    from AntShares.IO.MemoryStream import MemoryStream
"""


from io import BytesIO
from binascii import hexlify


class MemoryStream(BytesIO):
    """docstring for MemoryStream"""
    def __init__(self):
        super(MemoryStream, self).__init__()

    def canRead(self):
        return self.readable

    def canSeek(self):
        return self.seekable

    def canWrite(self):
        return self.writable

    def toArray(self):
        return hexlify(self.getvalue())
