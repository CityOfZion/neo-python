from neo.Utils.NeoTestCase import NeoTestCase
from neo.Cryptography import Helper


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
