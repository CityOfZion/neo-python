# -*- coding: UTF-8 -*-
import hashlib
import binascii
from ecdsa import SigningKey, NIST256p,VerifyingKey
from .Helper import *
from neo.UInt256 import UInt256
from neo.UInt160 import UInt160
import bitcoin
from neo.Cryptography.ECCurve import EllipticCurve




class Crypto(object):

    @staticmethod
    def SetupSignatureCurve():

        bitcoin.change_curve(
            int("FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF", 16),
            int("FFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551", 16),
            int("FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC", 16),
            int("5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B", 16),
            int("6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296", 16),
            int("4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5", 16)
        )




    @staticmethod
    def Default():
        return CryptoInstance()

    @staticmethod
    def Hash160(message):
        return bin_hash160(message)

    @staticmethod
    def Hash160Bytes(message):
        return bin_hash160Bytes(message)

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

        Crypto.SetupSignatureCurve()

        hash = hashlib.sha256(binascii.unhexlify(message)).hexdigest()

        v,r,s = bitcoin.ecdsa_raw_sign(hash, private_key)

        rb = bytearray(r.to_bytes(32, 'big'))
        sb = bytearray(s.to_bytes(32, 'big'))

        sig = rb + sb

        return sig

    @staticmethod
    def VerifySignature(message, signature, public_key):

        Crypto.SetupSignatureCurve()

        if type(public_key) is EllipticCurve.ECPoint:

            pubkey_x = public_key.x.value.to_bytes(32,'big')
            pubkey_y = public_key.y.value.to_bytes(32,'big')

            public_key = pubkey_x + pubkey_y

        m = message
        try:
            m = binascii.unhexlify(message)
        except Exception as e:
            print("could not get m")

        if len(public_key) == 33:

            public_key = bitcoin.decompress(public_key)
            public_key = public_key[1:]

        try:
            vk = VerifyingKey.from_string( public_key,curve=NIST256p, hashfunc=hashlib.sha256 )
            res = vk.verify(signature, m,hashfunc=hashlib.sha256)
            return res
        except Exception as e:
            pass

        return False


class CryptoInstance():

    def Hash160(self, message):
        return Crypto.Hash160Bytes(message)

    def Hash256(self, message):
        return Crypto.Hash256(message)

    def Sign(self, message, prikey, pubkey):
        return Crypto.Sign(message, prikey, pubkey)

    def VerifySignature(self, message, signature, pubkey):
        return Crypto.VerifySignature(message, signature, pubkey)