# -*- coding:utf-8 -*-
"""
Description:
    MemoryStream
Usage:
    from neo.IO.MemoryStream import MemoryStream
"""


from io import BytesIO
from binascii import hexlify


class MemoryStream(BytesIO):
    """docstring for MemoryStream"""
    def __init__(self, *args, **kwargs):
        super(MemoryStream, self).__init__(*args, **kwargs)

    def canRead(self):
        return self.readable

    def canSeek(self):
        return self.seekable

    def canWrite(self):
        return self.writable

    def ToArray(self):
        return hexlify(self.getvalue())

    def Cleanup(self):
        self.seek(0)
        self.truncate()
        self.close()

