import binascii
from io import BytesIO
from unittest import TestCase
from neo.Core.Fixed8 import Fixed8
from neo.Core.UInt160 import UInt160
from neo.Core.UInt256 import UInt256
from neo.Core.IO.Mixins import SerializableMixin
import neo.Core.IO.BinaryWriter as BinaryWriter
from neo.Core.IO.BinaryReader import BinaryReader


class TestObject(SerializableMixin):
    test_value = None

    def __init__(self, test_value=None):
        self.test_value = test_value

    def Serialize(self, writer):
        writer.WriteUInt32(self.test_value)

    def Deserialize(self, reader):
        self.test_value = reader.ReadUInt32()

    def ToArray(self):
        pass


class SerializableMixinTestCase(TestCase):
    def test_serializable_mixin(self):
        m = SerializableMixin()
        m.Serialize(None)
        m.Deserialize(None)
        m.ToArray()


def get_br(stream_data):
    return BinaryReader(BytesIO(stream_data))


def get_bw(stream_data):
    return BinaryWriter.BinaryWriter(BytesIO(stream_data))


class BinaryReaderTestCase(TestCase):
    def setUp(self):
        stream = BytesIO(b"\x41\x01\x02\x03\x04")
        self.br = BinaryReader(stream)

    def test_various(self):
        self.assertEqual(self.br.unpack("c"), b"A")

        b = self.br.ReadByte()
        self.assertEqual(b, b'\x01')

        b = self.br.ReadByte()
        self.assertEqual(b, b"\x02")

        bio0 = BytesIO(b"")
        br0 = BinaryReader(bio0)
        with self.assertRaises(ValueError):
            br0.ReadByte()

        b = self.br.ReadBool()
        self.assertEqual(b, True)

        self.assertEqual(get_br(b"\x41").ReadChar(), b"A")

        self.assertEqual(get_br(b"1234").ReadFloat(), 1.6688933612840628e-07)
        self.assertEqual(get_br(b"12345678").ReadDouble(), 6.821320051701325e-38)
        self.assertEqual(get_br(b"12").ReadInt8(), 49)
        self.assertEqual(get_br(b"12").ReadUInt8(), 49)
        self.assertEqual(get_br(b"12").ReadInt16(), 12849)
        self.assertEqual(get_br(b"12").ReadUInt16(), 12849)
        self.assertEqual(get_br(b"\xff234").ReadInt32(), 875770623)
        self.assertEqual(get_br(b"\xff234").ReadUInt32(), 875770623)
        self.assertEqual(get_br(b"12345678").ReadInt64(), 4050765991979987505)
        self.assertEqual(get_br(b"12345678").ReadUInt64(), 4050765991979987505)

        self.assertEqual(get_br(b"\x03234").ReadString(), b"234")
        self.assertEqual(get_br(b"\x03123").ReadVarString(), b"123")
        self.assertEqual(get_br(b"abc").ReadFixedString(2), b"ab")

        x = get_br(b"123871987392873918723981723987189").ReadUInt256()
        self.assertEqual(str(x), "3831373839333237313839333237383139333738323933373839313738333231")

        x = get_br(b"123871987392873918723981723987189").ReadUInt160()
        self.assertEqual(str(x), "3237383139333738323933373839313738333231")

        x = get_br(b"\x01\x02\x0345678").ReadFixed8()
        self.assertEqual(str(x), "40507659919.76829529")

        self.assertEqual(get_br(b"\x0212345567898765434567890987").ReadHashes(), ['3738393039383736353433343536373839383736353534333231', ''])

    def test_varint(self):
        self.assertEqual(get_br(b"").ReadVarInt(), 0)
        self.assertEqual(get_br(b"\xfd12").ReadVarInt(), 12849)
        self.assertEqual(get_br(b"\xfe1234").ReadVarInt(), 875770417)
        self.assertEqual(get_br(b"\xff12345678").ReadVarInt(), 4050765991979987505)

        with self.assertRaises(ValueError) as context:
            self.assertEqual(get_br(b"\xfd1234").ReadVarInt(max=12848), 12849)
            self.assertIn("Maximum number of bytes (12848) exceeded.", context)

    def test_Read2000256List(self):
        val = b"1" * 64
        x = get_br(val * 2000)
        res = x.Read2000256List()
        for item in res:
            self.assertEqual(item, val)

    def test_readserializable_success(self):
        stream = BytesIO(b"\x04\x01\x02\x03\x04")
        reader = BinaryReader(stream)
        test_object_list = reader.ReadSerializableArray('neo.Core.tests.test_io.TestObject')
        self.assertEqual(test_object_list[0].test_value, 0x4030201)

    def test_readserializable_fail(self):
        # fails because input stream is too short
        stream = BytesIO(b"\x04\x01\x02\x03")
        reader = BinaryReader(stream)
        test_object_list = reader.ReadSerializableArray('neo.Core.tests.test_io.TestObject')
        self.assertEqual(len(test_object_list), 0)

    def test_readvarint_fail(self):
        stream = BytesIO(b"")
        reader = BinaryReader(stream)
        result = reader.ReadVarInt()
        self.assertEqual(result, 0)

    def test_saferead(self):
        self.assertNotEqual(len(get_br(b"1234").ReadBytes(10)), 10)
        with self.assertRaises(ValueError) as context:
            get_br(b"1234").SafeReadBytes(10)
        self.assertIn("Not enough data available", str(context.exception))
        self.assertEqual(len(get_br(b"\x01\x02\x03\x04\x05\x06\x07\x08").SafeReadBytes(8)), 8)

    def test_readvarbytes_insufficient_data(self):
        """expect 1 byte, have 0"""
        with self.assertRaises(ValueError) as context:
            get_br(b"\xfd\x01\x00").ReadVarBytes()
        self.assertIn("Not enough data available", str(context.exception))


class BinaryWriterTestCase(TestCase):
    def test_various(self):
        self.assertEqual(BinaryWriter.swap32(123), 2063597568)
        self.assertEqual(BinaryWriter.swap32(2063597568), 123)

        self.assertEqual(BinaryWriter.convert_to_uint160(123), '00000000000001111011')
        self.assertEqual(BinaryWriter.convert_to_uint256(123), '00000000000000000000000001111011')

        def bw_writebyte(stream_data):
            stream = BytesIO()
            bw = BinaryWriter.BinaryWriter(stream)
            bw.WriteByte(stream_data)
            stream.seek(0)
            return stream

        self.assertEqual(bw_writebyte(b'\x00').read(1), b'\x00')
        self.assertEqual(bw_writebyte('1').read(1), b'1')
        self.assertEqual(bw_writebyte(1).read(1), b'\x01')

        def bw_setup():
            stream = BytesIO()
            bw = BinaryWriter.BinaryWriter(stream)
            return stream, bw

        stream, bw = bw_setup()
        bw.pack('c', b'\x41')
        stream.seek(0)
        self.assertEqual(stream.read(1), b'A')

        stream, bw = bw_setup()
        bw.WriteChar(b'\x41')
        stream.seek(0)
        self.assertEqual(stream.read(1), b'A')

        stream, bw = bw_setup()
        bw.WriteFloat(123.41)
        stream.seek(0)
        self.assertEqual(stream.readline(), b'\xec\xd1\xf6B')

        stream, bw = bw_setup()
        bw.WriteDouble(976)
        stream.seek(0)
        self.assertEqual(stream.readline(), b'\x00\x00\x00\x00\x00\x80\x8e@')

        stream, bw = bw_setup()
        bw.WriteUInt8(167)
        stream.seek(0)
        self.assertEqual(stream.readline(), b'\xa7')

        stream, bw = bw_setup()
        bw.WriteBool(True)
        stream.seek(0)
        self.assertEqual(stream.readline(), b'\x01')

        stream, bw = bw_setup()
        bw.WriteBool(False)
        stream.seek(0)
        self.assertEqual(stream.readline(), b'\x00')

        stream, bw = bw_setup()
        bw.WriteInt8(17)
        stream.seek(0)
        self.assertEqual(stream.readline(), b'\x11')

        stream, bw = bw_setup()
        bw.WriteInt16(12345)
        stream.seek(0)
        self.assertEqual(stream.readline(), b'90')

        stream, bw = bw_setup()
        bw.WriteUInt16(12345)
        stream.seek(0)
        self.assertEqual(stream.readline(), b'90')

        stream, bw = bw_setup()
        bw.WriteUInt16(32767 * 2)
        stream.seek(0)
        self.assertEqual(stream.readline(), b'\xfe\xff')

        stream, bw = bw_setup()
        bw.WriteInt32(32767 * 2 * 2)
        stream.seek(0)
        self.assertEqual(stream.readline(), b'\xfc\xff\x01\x00')

        stream, bw = bw_setup()
        bw.WriteUInt32(32767 * 2 * 2)
        stream.seek(0)
        self.assertEqual(stream.readline(), b'\xfc\xff\x01\x00')

        stream, bw = bw_setup()
        bw.WriteInt64(32767 * 2 * 2)
        stream.seek(0)
        self.assertEqual(stream.readline(), b'\xfc\xff\x01\x00\x00\x00\x00\x00')

        stream, bw = bw_setup()
        bw.WriteUInt64(32767 * 2 * 2)
        stream.seek(0)
        self.assertEqual(stream.readline(), b'\xfc\xff\x01\x00\x00\x00\x00\x00')

        stream, bw = bw_setup()
        bw.WriteUInt160(UInt160(b'12345678901234567890'))
        stream.seek(0)
        self.assertEqual(stream.readline(), b'\x124Vx\x90\x124Vx\x90')

        with self.assertRaises(TypeError):
            bw.WriteUInt160(123)

        stream, bw = bw_setup()
        bw.WriteUInt256(UInt256(b'12345678901234567890123456789012'))
        stream.seek(0)
        self.assertEqual(stream.readline(), b'\x124Vx\x90\x124Vx\x90\x124Vx\x90\x12')

        with self.assertRaises(TypeError):
            bw.WriteUInt256(123)

        with self.assertRaises(TypeError):
            bw.WriteVarInt("x")

        with self.assertRaises(ValueError):
            bw.WriteVarInt(-1)

        stream, bw = bw_setup()
        bw.WriteVarInt(12)
        stream.seek(0)
        self.assertEqual(stream.readline(), b'\x0c')

        stream, bw = bw_setup()
        bw.WriteVarInt(0xff)
        stream.seek(0)
        self.assertEqual(stream.readline(), b'\xfd\xff\x00')

        stream, bw = bw_setup()
        bw.WriteVarInt(0xffffff)
        stream.seek(0)
        self.assertEqual(stream.readline(), b'\xfe\xff\xff\xff\x00')

        stream, bw = bw_setup()
        bw.WriteVarInt(0xFFFFFFFFFF)
        stream.seek(0)
        self.assertEqual(stream.readline(), b'\xff\xff\xff\xff\xff\xff\x00\x00\x00')

        stream, bw = bw_setup()
        bw.WriteVarBytes(b'123')
        stream.seek(0)
        self.assertEqual(stream.readline(), b'\x03123')

        stream, bw = bw_setup()
        bw.WriteFixedString("test", 10)
        stream.seek(0)
        self.assertEqual(stream.readline(), b'test\x00\x00\x00\x00\x00\x00')

        stream, bw = bw_setup()
        bw.WriteSerializableArray(None)
        stream.seek(0)
        self.assertEqual(stream.readline(), b'\x00')

        # stream, bw = bw_setup()
        # val = [b'x' * 64 for _ in range(2000)]
        # bw.Write2000256List(val)
        # stream.seek(0)
        # self.assertEqual(stream.readline(), b'\x00')

        stream, bw = bw_setup()
        bw.WriteHashes([b'12', b'45'])
        stream.seek(0)
        self.assertEqual(stream.readline(), b'\x02\x12E')

        stream, bw = bw_setup()
        bw.WriteFixed8(Fixed8(100))
        stream.seek(0)
        self.assertEqual(stream.readline(), b'd\x00\x00\x00\x00\x00\x00\x00')

        #
        stream, bw = bw_setup()
        test_value = "my_test_string"
        bw.WriteVarString(test_value)
        stream.seek(0)
        result = stream.readline()
        # note \x0e is the length of `test_value` that's appended in front
        self.assertEqual(b'\x0emy_test_string', result)

    def test_Write2000256List(self):
        item = b'aa' * 32
        my_list = [item] * 2000

        stream = BytesIO()
        bw = BinaryWriter.BinaryWriter(stream)
        bw.Write2000256List(my_list)

        stream.seek(0)
        for i in range(0, 2000):
            x = binascii.hexlify(stream.readline(32))
            self.assertEqual(item, x)

    def test_write_serializable_array(self):
        my_array = [TestObject(1), TestObject(2)]

        stream = BytesIO()
        bw = BinaryWriter.BinaryWriter(stream)
        bw.WriteSerializableArray(my_array)

        stream.seek(0)
        reader = BinaryReader(stream)
        test_object_list = reader.ReadSerializableArray('neo.Core.tests.test_io.TestObject')
        self.assertEqual(0x1, test_object_list[0].test_value)
        self.assertEqual(0x2, test_object_list[1].test_value)

    def test_writefixedstring_exception(self):
        stream = BytesIO()
        bw = BinaryWriter.BinaryWriter(stream)

        with self.assertRaises(ValueError) as context:
            bw.WriteFixedString("abc", 2)
        self.assertIn("String 'abc' length is longer than fixed length: 2", str(context.exception))
