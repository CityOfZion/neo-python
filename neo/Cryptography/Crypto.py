# -*- coding: UTF-8 -*-
import hashlib
import binascii
from ecdsa import SigningKey, NIST256p,VerifyingKey
from .Helper import *
class Crypto(object):

    @staticmethod
    def Hash160(message):
        return bin_hash160(message)
#        msg = hashlib.sha256(message)
#        hash = hashlib.new('ripemd160')
#        hash.update(msg)
#        return hash.hexdigest()

    @staticmethod
    def Hash256(message):
        return hashlib.sha256(hashlib.sha256(message))

    @staticmethod
    def Sign(message, private_key, public_key):

        sk = SigningKey.from_string(binascii.unhexlify(private_key), curve=NIST256p, hashfunc=hashlib.sha256)
        signature = binascii.hexlify(sk.sign( message, hashfunc=hashlib.sha256))

        return signature

    @staticmethod
    def VerifySignature(message, signature, public_key):

        vk = VerifyingKey.from_string( binascii.unhexlify(public_key),curve=NIST256p, hashfunc=hashlib.sha256 )
        return vk.verify(binascii.unhexlify(signature), message)

