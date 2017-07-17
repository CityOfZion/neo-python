from bitarray import bitarray
import ecdsa
from bitcoin import privkey_to_pubkey
from neo.Cryptography.Helper import pubkey_to_redeem,redeem_to_scripthash

class KeyPair(object):

    PublicKeyHash = None

    PublicKey = bitarray()

    PrivateKey = bitarray()

    def __init__(self, private_key):
        self.PrivateKey = private_key

        self.PublicKey = privkey_to_pubkey(self.PrivateKey)

        self.PublicKeyHash = redeem_to_scripthash( pubkey_to_redeem(self.PublicKey))

