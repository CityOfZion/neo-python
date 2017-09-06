import bitcoin
from neo.Cryptography.ECCurve import ECDSA,EllipticCurve,FiniteField
from neo.Cryptography.Crypto import Crypto
import base58
import bitcoin
import binascii

class KeyPair(object):

    PublicKeyHash = None

    PublicKey = None

    PrivateKey = None



    def setup_curve(self):
#        bitcoin.change_curve(
#            int("FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF", 16),
#            int("FFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551", 16),
#            int("FFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC", 16),
#            int("5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B", 16),
#            int("6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296", 16),
#            int("4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5", 16)
#        )
        bitcoin.change_curve(
            115792089210356248762697446949407573530086143415290314195533631308867097853951,
            115792089210356248762697446949407573529996955224135760342422259061068512044369,
            115792089210356248762697446949407573530086143415290314195533631308867097853948,
            41058363725152142129326129780047268409114441015993725554835256314039467401291,
            48439561293906451759052585252797914202762949526041747995844080717082404635286,
            36134250956749795798585127919587881956611106672985015071877198253568414405109
        )


    def __init__(self, priv_key):


        self.setup_curve()

        length = len(priv_key)

        if length != 32 and length != 96 and length != 104:
            raise Exception("Invalid private key")

        self.PrivateKey = bytearray(priv_key[-32:])

        pubkey_encoded_not_compressed = None

        if length == 32:

            pubkey_encoded_not_compressed = bitcoin.privkey_to_pubkey(priv_key)

        elif length == 64 or length == 72:
            skip = length - 64
            pubkey_encoded_not_compressed = bytearray(b'04').hex() + priv_key[skip:]

        elif length == 96 or length == 104:
            skip = length - 96
            pubkey_encoded_not_compressed = bytearray(b'\x04') + bytearray(priv_key[skip:skip + 64])

        if pubkey_encoded_not_compressed:
            pubkey_points = bitcoin.decode_pubkey(pubkey_encoded_not_compressed, 'bin')

            pubx = pubkey_points[0]
            puby = pubkey_points[1]
            edcsa = ECDSA.secp256r1()
            self.PublicKey = edcsa.Curve.point(pubx, puby)

        else:
            raise Exception("Could not determine public key")

        self.PublicKeyHash = Crypto.ToScriptHash(self.PublicKey.encode_point(True), unhex=True)



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