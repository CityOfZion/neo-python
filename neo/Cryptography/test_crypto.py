from neo.Utils.NeoTestCase import NeoTestCase
from neo.Cryptography.Crypto import Crypto
from neo.Cryptography import Helper
from neo.Settings import settings

from neo.UInt160 import UInt160

class HelperTestCase(NeoTestCase):
    def test_xor_bytes(self):
        a = b"12345"
        b = b"09876"
        expected_result = b'\x01\x0b\x0b\x03\x03'

        # Should work
        result = Helper.xor_bytes(a, b)
        self.assertEqual(result, expected_result)

        # Should not work on inequal length byte objects
        with self.assertRaises(AssertionError) as context:
            Helper.xor_bytes(a, b"x")

    def test_base256_encode(self):
        val = 1234567890
        res = Helper.base256_encode(val)
        self.assertEqual(res, bytearray(b'\xd2\x02\x96I'))

    def test_random_key(self):
        a = Helper.random_key()
        self.assertEqual(len(a), 64)

        b = Helper.random_key()
        self.assertNotEqual(a, b)

    def test_to_address(self):
        script_hash = UInt160(data=b'B\x11#x\xff\xa3,Le\xd5\x13\xaa5\x06\x89\xdf\xf68\x11T')
        self.assertEqual(Crypto.ToAddress(script_hash), 'AMoCmy4xaaCnpejTAJkZYTsRz58BLopeeV')

    def test_to_address_alt_version(self):
        original_version = settings.ADDRESS_VERSION
        settings.ADDRESS_VERSION = 42

        script_hash = UInt160(data=b'B\x11#x\xff\xa3,Le\xd5\x13\xaa5\x06\x89\xdf\xf68\x11T')
        self.assertEqual(Crypto.ToAddress(script_hash), 'J1DfV2jS511SMtP6dH5ckr3Nwf26kbFx7s')

        settings.ADDRESS_VERSION = original_version
