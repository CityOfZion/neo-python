# -*- coding: UTF-8 -*-
import hashlib
import binascii
from ecdsa import SigningKey, NIST256p,VerifyingKey
from .Helper import *
from neo.UInt256 import UInt256
from neo.UInt160 import UInt160

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
        return bin_dbl_sha256(message)
#        return hashlib.sha256(hashlib.sha256(message))

    @staticmethod
    def ToScriptHash(data):
        if len(data) > 1:
            data = binascii.unhexlify(data)
        return UInt160( data = binascii.unhexlify(bytes(Crypto.Hash160(data), encoding='utf-8')))

    @staticmethod
    def ToAddress(uint160):
        return hash_to_wallet_address(uint160.Data)

    @staticmethod
    def Sign(message, private_key, public_key):

        sk = SigningKey.from_string(binascii.unhexlify(private_key), curve=NIST256p, hashfunc=hashlib.sha256)
        signature = binascii.hexlify(sk.sign( message, hashfunc=hashlib.sha256))

        return signature

    @staticmethod
    def VerifySignature(message, signature, public_key):

        vk = VerifyingKey.from_string( binascii.unhexlify(public_key),curve=NIST256p, hashfunc=hashlib.sha256 )
        return vk.verify(binascii.unhexlify(signature), message)

