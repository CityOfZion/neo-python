# -*- coding:utf-8 -*-
"""
Description:
    MemoryStream
Usage:
    from neo.IO.MemoryStream import MemoryStream
"""


from io import BytesIO
from binascii import hexlify


__mstreams__ = []
__mstreams_available__ = []


class StreamManager(object):

    @staticmethod
    def TotalBuffers():
        return len(__mstreams__)

    @staticmethod
    def GetStream(data=None):

        if len(__mstreams_available__) == 0:
            if data:
                mstream = MemoryStream(data)
                mstream.seek(0)
            else:
                mstream = MemoryStream()
            __mstreams__.append(mstream)
            return mstream

        mstream = __mstreams_available__.pop()

        if data is not None and len(data):
            mstream.Cleanup()
            mstream.write(data)

        mstream.seek(0)

        return mstream

    @staticmethod
    def ReleaseStream(mstream):
        mstream.Cleanup()
        __mstreams_available__.append(mstream)


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
        self.truncate(0)
