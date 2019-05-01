import bitcoin
from ecdsa import NIST256p, VerifyingKey
from .Helper import *
from neo.Core.UInt160 import UInt160
from .ECCurve import EllipticCurve


class Crypto(object):

    _Instance = None

    @staticmethod
    def SetupSignatureCurve():
        """
        Setup the Elliptic curve parameters.
        """
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
        """
        Get the default Crypto instance.

        Returns:
            CryptoInstance:
        """
        if not Crypto._Instance:
            Crypto._Instance = CryptoInstance()
        return Crypto._Instance

    @staticmethod
    def Hash160(message):
        """
        Get a hash of the provided message using the ripemd160 algorithm.
        Args:
            message (str): message to hash.

        Returns:
            str: hash as a double digit hex string.
        """
        return bin_hash160(message)

    @staticmethod
    def Hash160Bytes(message):
        """
        Get a hash of the provided message using the ripemd160 algorithm.
        Args:
            message (str): message to hash.

        Returns:
            bytes: hash.
        """
        return bin_hash160Bytes(message)

    @staticmethod
    def Hash256(message):
        """
        Get a the hash of a double SHA256 operation on the message. i.e. SHA256(SHA256(message))

        Args:
            message (str): message to hash.

        Returns:
            bytes: hash.
        """
        return bin_dbl_sha256(message)

    @staticmethod
    def ToScriptHash(data, unhex=True):
        """
        Get a script hash of the data.

        Args:
            data (bytes): data to hash.
            unhex (bool): (Default) True. Set to unhexlify the stream. Use when the bytes are not raw bytes; i.e. b'aabb'

        Returns:
            UInt160: script hash.
        """
        if len(data) > 1 and unhex:
            data = binascii.unhexlify(data)
        return UInt160(data=binascii.unhexlify(bytes(Crypto.Hash160(data), encoding='utf-8')))

    @staticmethod
    def ToAddress(script_hash):
        """
        Get the public address of the script hash.

        Args:
            script_hash (UInt160):

        Returns:
            str: base58 encoded string representing the wallet address.
        """
        return scripthash_to_address(script_hash.Data)

    @staticmethod
    def Sign(message, private_key):
        """
        Sign the message with the given private key.

        Args:
            message (hexstr): message to be signed
            private_key (str): 32 byte key as a double digit hex string (e.g. having a length of 64)
        Returns:
            bytearray: the signature of the message.
        """
        Crypto.SetupSignatureCurve()

        hash = hashlib.sha256(binascii.unhexlify(message)).hexdigest()

        v, r, s = bitcoin.ecdsa_raw_sign(hash, private_key)

        rb = bytearray(r.to_bytes(32, 'big'))
        sb = bytearray(s.to_bytes(32, 'big'))

        sig = rb + sb

        return sig

    @staticmethod
    def VerifySignature(message, signature, public_key, unhex=True):
        """
        Verify the integrity of the message.

        Args:
            message (hexstr or str): the message to verify.
            signature (bytearray): the signature belonging to the message.
            public_key (ECPoint|bytes): the public key to use for verifying the signature. If `public_key` is of type bytes then it should be raw bytes (i.e. b'\xAA\xBB').
            unhex (bool): whether the message should be unhexlified before verifying

        Returns:
            bool: True if verification passes. False otherwise.
        """

        if type(public_key) is EllipticCurve.ECPoint:
            pubkey_x = public_key.x.value.to_bytes(32, 'big')
            pubkey_y = public_key.y.value.to_bytes(32, 'big')

            public_key = pubkey_x + pubkey_y

        if unhex:
            try:
                message = binascii.unhexlify(message)
            except binascii.Error:
                pass
        elif isinstance(message, str):
            message = message.encode('utf-8')

        if len(public_key) == 33:
            public_key = bitcoin.decompress(public_key)
            public_key = public_key[1:]

        try:
            vk = VerifyingKey.from_string(public_key, curve=NIST256p, hashfunc=hashlib.sha256)
            res = vk.verify(signature, message, hashfunc=hashlib.sha256)
            return res
        except Exception:
            pass

        return False


class CryptoInstance():

    def __init__(self):
        Crypto.SetupSignatureCurve()

    def Hash160(self, message):
        """
        Get a hash of the provided message using the ripemd160 algorithm.
        Args:
            message (str): message to hash.

        Returns:
            str: hash as a double digit hex string.
        """
        return Crypto.Hash160Bytes(message)

    def Hash256(self, message):
        """
        Get a the hash of a double SHA256 operation on the message. i.e. SHA256(SHA256(message))

        Args:
            message (str): message to hash.

        Returns:
            bytes: hash.
        """
        return Crypto.Hash256(message)

    def Sign(self, message, private_key):
        """
        Sign the message with the given private key.

        Args:
            message (str): message to be signed
            private_key (str): 32 byte key as a double digit hex string (e.g. having a length of 64)

        Returns:
            bytearray: the signature of the message.
        """
        return Crypto.Sign(message, private_key)

    def VerifySignature(self, message, signature, public_key, unhex=True):
        """
        Verify the integrity of the message.

        Args:
            message (str): the message to verify.
            signature (bytearray): the signature belonging to the message.
            public_key (ECPoint): the public key to use for verifying the signature.
            unhex (bool): whether the message should be unhexlified before verifying

        Returns:
            bool: True if verification passes. False otherwise.
        """
        return Crypto.VerifySignature(message, signature, public_key, unhex=unhex)
