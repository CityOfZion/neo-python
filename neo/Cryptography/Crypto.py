# -*- coding: UTF-8 -*-
import hashlib
import binascii
from ecdsa import SigningKey, NIST256p,VerifyingKey
from .Helper import *
from neo.UInt256 import UInt256
from neo.UInt160 import UInt160



class Crypto(object):

    @staticmethod
    def Default():
        return CryptoInstance()

    @staticmethod
    def Hash160(message):
        return bin_hash160(message)


    @staticmethod
    def Hash256(message):
        return bin_dbl_sha256(message)
#        return hashlib.sha256(hashlib.sha256(message))

    @staticmethod
    def ToScriptHash(data, unhex=True):
        if len(data) > 1 and unhex:
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


class CryptoInstance():

    def Hash160(self, message):
        return Crypto.Hash160(message)

    def Hash256(self, message):
        return Crypto.Hash256(message)

    def Sign(self, message, prikey, pubkey):
        return Crypto.Sign(message, prikey, pubkey)

    def VerifySignature(self, message, signature, pubkey):
        return Crypto.VerifySignature(message, signature, pubkey)