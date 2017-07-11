# -*- coding:utf-8 -*-
"""
Description:
    Cryptography Helper
Usage:
    from neo.Cryptography.Helper import *
"""


import binascii
from bitcoin import *

def random_to_priv(key):
    return binascii.hexlify(key)

def pubkey_to_redeem(pubkey):
    return binascii.unhexlify('21'+ pubkey) + from_int_to_byte(int('ac',16))

def redeem_to_scripthash(redeem):
    return binascii.hexlify(bin_hash160(redeem))

def scripthash_to_address(scripthash):
    return bin_to_b58check(binascii.unhexlify(scripthash),int('17',16))