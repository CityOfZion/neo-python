"""
Description:
    Core Helper
Usage:
    from AntShares.Core.Helper import *
"""


def big_or_little(string):
    arr = bytearray(string)
    length = len(arr)
    for idx in xrange(length/2):
        if idx%2 == 0:
            arr[idx], arr[length-2-idx] = arr[length-2-idx], arr[idx]
        else:
            arr[idx], arr[length - idx] = arr[length - idx], arr[idx]
    return bytes(arr)
