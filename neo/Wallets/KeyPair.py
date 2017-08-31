import bitcoin
from neo.Cryptography.ECCurve import ECDSA,EllipticCurve,FiniteField
from neo.Cryptography.Crypto import Crypto
import base58

class KeyPair(object):

    PublicKeyHash = None

    PublicKey = None

    PrivateKey = None

    def __init__(self, priv_key):

        length = len(priv_key)

        if length != 32 and length != 96 and length != 104:
            raise Exception("Invalid private key")

        self.PrivateKey = bytearray(priv_key[-32:])


        if length == 32:
            pkint = int.from_bytes(self.PrivateKey, 'big')
            ecd = ECDSA.secp256r1()
            self.PublicKey = ecd.G * pkint

        encoded = self.PublicKey.encode_point(True)

        self.PublicKeyHash = Crypto.Hash160(encoded)


    @staticmethod
    def PrivateKeyFromWIF(wif):

        if wif is None:
            raise Exception('Please provide wif')
        data = base58.b58decode(wif)

        length = len(data)

        if length is not 38 and data[0] is not 0x80 and data[33] is not 0x01:
            raise Exception("Invalid format!")

        checksum = Crypto.Hash256(data[0:34])[0:4]

        if checksum != data[34:]:
            raise Exception("Invalid WIF Checksum")

        return data[1:33]


    def Export(self):


        data = bytearray(38)

        data[0] = 0x80
        data[1:33] = self.PrivateKey[0:32]
        data[33] = 0x01

        checksum= Crypto.Default().Hash256(data[0:34])
        data[34:38] = checksum[0:4]
        b58 = base58.b58encode(bytes(data))

        return b58