"""
Description:
    big_or_little
Usage:
    from AntShares.Helper import *
"""

ANTCOIN = 'f252a09a24591e8da31deec970871cc7678cb55023db049551e91f7bac28e27b'


def big_or_little(string):
    arr = bytearray(str(string))
    length = len(arr)
    for idx in xrange(length/2):
        if idx%2 == 0:
            arr[idx], arr[length-2-idx] = arr[length-2-idx], arr[idx]
        else:
            arr[idx], arr[length - idx] = arr[length - idx], arr[idx]
    return bytes(arr)
