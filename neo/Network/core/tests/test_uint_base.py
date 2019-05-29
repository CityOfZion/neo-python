from unittest import TestCase
from neo.Network.core.uintbase import UIntBase


class UIntBaseTest(TestCase):
    def test_create_with_empty_data(self):
        x = UIntBase(num_bytes=2)
        self.assertEqual(len(x._data), 2)
        self.assertEqual(x._data, b'\x00\x00')

    def test_valid_data(self):
        x = UIntBase(num_bytes=2, data=b'aabb')
        # test for proper conversion to raw bytes
        self.assertEqual(len(x._data), 2)
        self.assertNotEqual(len(x._data), 4)

        x = UIntBase(num_bytes=3, data=bytearray.fromhex('aabbcc'))
        self.assertEqual(len(x._data), 3)
        self.assertNotEqual(len(x._data), 6)

    def test_valid_rawbytes_data(self):
        x = UIntBase(num_bytes=2, data=b'\xaa\xbb')
        self.assertEqual(len(x._data), 2)
        self.assertNotEqual(len(x._data), 4)

    def test_invalid_data_type(self):
        with self.assertRaises(TypeError) as context:
            x = UIntBase(num_bytes=2, data='abc')
        self.assertTrue("Invalid data type" in str(context.exception))

    def test_raw_data_that_can_be_decoded(self):
        """
        some raw data can be decoded e.g. bytearray.fromhex('1122') but shouldn't be
        """
        tricky_raw_data = bytes.fromhex('1122')
        x = UIntBase(num_bytes=2, data=tricky_raw_data)
        self.assertEqual(x._data, tricky_raw_data)

    def test_data_length_mistmatch(self):
        with self.assertRaises(ValueError) as context:
            x = UIntBase(num_bytes=2, data=b'aa')  # 2 != 1
        self.assertTrue("Invalid UInt: data length" in str(context.exception))

    def test_size_property(self):
        x = UIntBase(num_bytes=2, data=b'\xaa\xbb')
        self.assertEqual(x.size, 2)

    def test_hash_code(self):
        x = UIntBase(num_bytes=4, data=bytearray.fromhex('DEADBEEF'))
        self.assertEqual(x.get_hash_code(), 4022250974)
        x = UIntBase(num_bytes=2, data=bytearray.fromhex('1122'))
        self.assertEqual(x.get_hash_code(), 8721)

    def test_serialize(self):
        pass

    def test_deserialize(self):
        pass

    def test_to_array(self):
        x = UIntBase(num_bytes=2, data=bytearray.fromhex('1122'))
        expected = b'\x11\x22'
        self.assertEqual(expected, x.to_array())

    def test_to_string(self):
        x = UIntBase(num_bytes=2, data=bytearray.fromhex('1122'))
        self.assertEqual('2211', x.to_string())
        self.assertEqual('2211', str(x))
        self.assertNotEqual('1122', x.to_string())
        self.assertNotEqual('1122', str(x))

    def test_equal(self):
        x = UIntBase(num_bytes=2, data=bytearray.fromhex('1122'))
        y = UIntBase(num_bytes=2, data=bytearray.fromhex('1122'))
        z = UIntBase(num_bytes=2, data=bytearray.fromhex('2211'))

        self.assertFalse(x is None)
        self.assertFalse(x == int(1122))
        self.assertTrue(x == x)
        self.assertTrue(x == y)
        self.assertTrue(x != z)

    def test_hash(self):
        x = UIntBase(num_bytes=2, data=bytearray.fromhex('1122'))
        y = UIntBase(num_bytes=2, data=bytearray.fromhex('1122'))
        z = UIntBase(num_bytes=2, data=bytearray.fromhex('2211'))
        self.assertEqual(hash(x), hash(y))
        self.assertNotEqual(hash(x), hash(z))

    def test_compare_to(self):
        x = UIntBase(num_bytes=2, data=bytearray.fromhex('1122'))
        y = UIntBase(num_bytes=3, data=bytearray.fromhex('112233'))
        z = UIntBase(num_bytes=2, data=bytearray.fromhex('1133'))
        xx = UIntBase(num_bytes=2, data=bytearray.fromhex('1122'))

        # test invalid type
        with self.assertRaises(TypeError) as context:
            x._compare_to(None)

        expected = "Cannot compare UIntBase to type NoneType"
        self.assertEqual(expected, str(context.exception))

        # test invalid length
        with self.assertRaises(ValueError) as context:
            x._compare_to(y)

        expected = "Cannot compare UIntBase with length 2 to UIntBase with length 3"
        self.assertEqual(expected, str(context.exception))

        # test data difference ('22' < '33')
        self.assertEqual(-1, x._compare_to(z))
        # test data difference ('33' > '22')
        self.assertEqual(1, z._compare_to(x))
        # test data equal
        self.assertEqual(0, x._compare_to(xx))

    def test_rich_comparison_methods(self):
        x = UIntBase(num_bytes=2, data=bytearray.fromhex('1122'))
        z = UIntBase(num_bytes=2, data=bytearray.fromhex('1133'))
        xx = UIntBase(num_bytes=2, data=bytearray.fromhex('1122'))

        self.assertTrue(x < z)
        self.assertTrue(z > x)
        self.assertTrue(x <= xx)
        self.assertTrue(x >= xx)
