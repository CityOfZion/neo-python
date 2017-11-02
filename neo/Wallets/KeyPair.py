import bitcoin
from neo.Cryptography.ECCurve import ECDSA
from neo.Cryptography.Crypto import Crypto
import base58


class KeyPair(object):

    PublicKeyHash = None

    PublicKey = None

    PrivateKey = None

    def setup_curve(self):

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

        if wif is None or len(wif) is not 52:
            raise ValueError('Please provide a wif with a length of 52 bytes (LEN: {0:d})'.format(len(wif)))

        data = base58.b58decode(wif)

        length = len(data)

        if length is not 38 or data[0] is not 0x80 or data[33] is not 0x01:
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

        checksum = Crypto.Default().Hash256(data[0:34])
        data[34:38] = checksum[0:4]
        b58 = base58.b58encode(bytes(data))

        return b58
