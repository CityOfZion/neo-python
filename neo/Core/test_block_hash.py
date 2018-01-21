from neo.Utils.NeoTestCase import NeoTestCase
import binascii
from neocore.Cryptography.Helper import *
from neocore.UInt256 import UInt256


class BlockHashTest(NeoTestCase):

    block_raw = b'00000000a291d73be4a7cf582c7cd9fb0c49bfca76c4fbb5881ea7906588f9f7acf69f2adc19cb001e0aa2b0024fda6baf3c77ddbb8ac90b39e42d76b69fa3830e52e902f2b480593e5d0500be9260c6e922bc7cf3812db982f3b0089a21a278988efeec6a027b25'

    uint256val = b'700d9c7f699d318d27d1600b7b1e3b9f636e9a71c3c6ad8a317eed3b5f8bba2e'

    rout = '2eba8b5f3bed7e318aadc6c3719a6e639f3b1e7b0b60d1278d319d697f9c0d70'

    def test_raw_to_hash(self):
        ba = bytearray(binascii.unhexlify(self.block_raw))
        hash = bin_dbl_sha256(ba)
        hashhex = binascii.hexlify(hash)

        self.assertEqual(hashhex, self.uint256val)

    def test_hash_to_s(self):

        uint256bytes = bytearray(binascii.unhexlify(self.uint256val))
        uint256bytes.reverse()
        out = uint256bytes.hex()

        self.assertEqual(out, self.rout)

    def test_raw_to_hash_to_s(self):

        ba = bytearray(binascii.unhexlify(self.block_raw))
        hash = bin_dbl_sha256(ba)
        hashhex = binascii.hexlify(hash)

        uint256bytes = bytearray(binascii.unhexlify(hashhex))
        uint256bytes.reverse()
        out = uint256bytes.hex()

        self.assertEqual(out, self.rout)
