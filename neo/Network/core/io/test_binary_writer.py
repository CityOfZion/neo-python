import unittest
from neo.Network.core.io.binary_writer import BinaryWriter


class BinaryWriterTest(unittest.TestCase):
    def test_var_string(self):
        data = "hello"
        b = BinaryWriter(stream=bytearray())
        b.write_var_string(data)
        self.assertTrue(data, b._stream.getvalue())
