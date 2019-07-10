import unittest
from neo.Network.core.io.binary_reader import BinaryReader


class BinaryReaderTest(unittest.TestCase):
    def test_initialization_with_bytearray(self):
        data = b'\xaa\xbb'
        x = BinaryReader(stream=bytearray(data))
        self.assertTrue(data, x._stream.getvalue())

    def test_reading_bytes(self):
        data = b'\xaa\xbb\xCC'
        x = BinaryReader(stream=bytearray(data))

        read_one = x.read_byte()
        self.assertEqual(1, len(read_one))
        self.assertEqual(b'\xaa', read_one)

        read_two = x.read_bytes(2)
        self.assertEqual(2, len(read_two))
        self.assertEqual(b'\xbb\xcc', read_two)

    def test_read_more_data_than_available(self):
        data = b'\xaa\xbb'
        x = BinaryReader(stream=bytearray(data))

        with self.assertRaises(ValueError) as context:
            x.read_bytes(3)
        expected_error = "Could not read 3 bytes from stream. Only found 2 bytes of data"
        self.assertEqual(expected_error, str(context.exception))

    def test_read_byte_from_empty_stream(self):
        x = BinaryReader(stream=bytearray())

        with self.assertRaises(ValueError) as context:
            x.read_byte()

        expected_error = "Could not read byte from empty stream"
        self.assertEqual(expected_error, str(context.exception))
