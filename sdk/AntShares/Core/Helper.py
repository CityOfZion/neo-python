"""
Description:
    Core Helper
Usage:
    from AntShares.Core.Helper import *
"""


def name_to_hex(name):
    return ''.join([hex(ord(x))[2:] for x in name])

def big_or_little(string):
    arr = bytearray(string)
    length = len(arr)
    for idx in xrange(length/2):
        if idx%2 == 0:
            arr[idx], arr[length-2-idx] = arr[length-2-idx], arr[idx]
        else:
            arr[idx], arr[length - idx] = arr[length - idx], arr[idx]
    return bytes(arr)

def float_2_hex(f):
    base = 0x10000000000000000
    return hex(base + int(f/0.00000001))[-17:-1]
