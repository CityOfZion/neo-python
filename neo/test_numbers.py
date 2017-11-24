from io import BytesIO

from neo.Utils.NeoTestCase import NeoTestCase
from neo.IO.BinaryWriter import BinaryWriter
from neo.IO.BinaryReader import BinaryReader

from neo.Fixed8 import Fixed8
from neo.BigInteger import BigInteger
from neo.UIntBase import UIntBase
from neo.UInt160 import UInt160
from neo.UInt256 import UInt256


class Fixed8TestCase(NeoTestCase):
    def test_fixed8_add(self):
        f1 = Fixed8(100)
        f2 = Fixed8(300)

        f3 = f1 + f2

        self.assertIsInstance(f3, Fixed8)
        self.assertEqual(f3.value, 400)

    def test_fixed8_sub(self):
        f1 = Fixed8(100)
        f2 = Fixed8(300)

        f3 = f1 - f2

        self.assertIsInstance(f3, Fixed8)
        self.assertEqual(f3.value, -200)

    def test_fixed8_mul(self):
        f1 = Fixed8(3)
        f2 = Fixed8(9)

        f3 = f1 * f2

        self.assertIsInstance(f3, Fixed8)
        self.assertEqual(f3.value, 27)

    def test_fixed8_div(self):
        f1 = Fixed8(27)
        f2 = Fixed8(3)

        f3 = f1 / f2

        self.assertIsInstance(f3, Fixed8)
        self.assertEqual(f3.value, 9)

    def test_fixed8_pow(self):
        f1 = Fixed8(2)
        f2 = Fixed8(3)

        f3 = pow(f1, f2)

        self.assertIsInstance(f3, Fixed8)
        self.assertEqual(f3.value, 8)

    def test_fixed8_mod(self):

        f1 = Fixed8(10)
        f2 = Fixed8(5)

        f3 = f1 % f2

        self.assertIsInstance(f3, Fixed8)
        self.assertEqual(f3.value, 0)

        f4 = Fixed8(7)

        f5 = f1 % f4

        self.assertEqual(f5.value, 3)

    def test_fixed8_neg(self):
        f1 = Fixed8(2)

        f1 = -f1
        self.assertIsInstance(f1, Fixed8)
        self.assertEqual(f1.value, -2)

    def test_from_decimal(self):
        decimal = 2042.02556
        f8 = Fixed8.FromDecimal(decimal)

        self.assertIsInstance(f8, Fixed8)
        self.assertEqual(f8.value, 204202556000)


class BigIntegerTestCase(NeoTestCase):
    def test_big_integer_add(self):
        b1 = BigInteger(10)
        b2 = BigInteger(20)

        b3 = b1 + b2

        self.assertIsInstance(b3, BigInteger)
        self.assertEqual(b3, 30)

    def test_big_integer_sub(self):
        b1 = BigInteger(5505505505505505050505)
        b2 = BigInteger(5505505505505505000000)

        b3 = b1 - b2

        self.assertIsInstance(b3, BigInteger)
        self.assertEqual(b3, 50505)

    def test_big_integer_mul(self):
        b1 = BigInteger(55055055055055)
        b2 = BigInteger(55055055055)

        b3 = b1 * b2

        self.assertIsInstance(b3, BigInteger)
        self.assertEqual(b3, 3031059087112109081053025)

    def test_big_integer_div(self):
        b1 = BigInteger(55055055055055)
        b2 = BigInteger(55055055)

        b3 = b1 / b2
        self.assertIsInstance(b3, BigInteger)
        self.assertEqual(b3, 1000000)

    def test_big_integer_float(self):
        b1 = BigInteger(5505.001)
        b2 = BigInteger(55055.999)

        b3 = b1 + b2

        self.assertIsInstance(b3, BigInteger)
        self.assertEqual(b3, 60560)

    def test_big_integer_to_ba(self):
        b1 = BigInteger(8972340892734890723)
        ba = b1.ToByteArray()

        integer = BigInteger.from_bytes(ba, 'little')
        self.assertEqual(integer, 8972340892734890723)

        b2 = BigInteger(-100)
        b2ba = b2.ToByteArray()
        integer2 = BigInteger.from_bytes(b2ba, 'little')
        self.assertEqual(integer2, 65436)

    def test_big_integer_frombytes(self):
        b1 = BigInteger(8972340892734890723)
        ba = b1.ToByteArray()

        b2 = BigInteger.FromBytes(ba)
        self.assertEqual(b1, b2)
        self.assertTrue(b1.Equals(b2))

    def test_big_integer_sign(self):

        b1 = BigInteger(3)
        b2 = BigInteger(0)
        b3 = BigInteger(-4)
        self.assertEqual(b1.Sign, 1)
        self.assertEqual(b2.Sign, 0)
        self.assertEqual(b3.Sign, -1)

        c1 = BigInteger(-100)
        c1_bytes = c1.ToByteArray()

        c2 = BigInteger.FromBytes(c1_bytes, signed=True)
        self.assertEqual(c2.Sign, -1)

        c2_unsigned = BigInteger.FromBytes(c1_bytes, signed=False)
        self.assertEqual(c2_unsigned.Sign, 1)


class UIntBaseTestCase(NeoTestCase):
    def test_initialization(self):
        u0 = UIntBase(0)
        self.assertEqual(hash(u0), 0)

        u1 = UIntBase(10)
        self.assertEqual(hash(u1), 0)

        u2 = UIntBase(3, bytearray(b'abc'))
        self.assertEqual(hash(u2), 6513249)

        u3 = UIntBase(3, b'abc')
        self.assertEqual(hash(u3), 6513249)

    def test_initialization_with_bytes(self):
        u1 = UIntBase(3, b'abc')
        self.assertEqual(hash(u1), 6513249)

    def test_initialization_with_bytearray(self):
        u1 = UIntBase(3, bytearray(b'abc'))
        self.assertEqual(hash(u1), 6513249)

    def test_initialization_with_invalid_datalen(self):
        with self.assertRaises(Exception):
            UIntBase(3, bytearray(b'abcd'))

    def test_initialization_with_invalid_datatype(self):
        with self.assertRaises(Exception):
            UIntBase(3, 'abc')

    def test_size(self):
        u1 = UIntBase(3, bytearray(b'abc'))
        self.assertEqual(u1.Size, 3)

    def test_serialize(self):
        data = b'abc'

        stream = BytesIO()
        u1 = UIntBase(3, bytearray(data))
        u1.Serialize(BinaryWriter(stream))
        self.assertEqual(stream.getvalue(), data)

        stream = BytesIO()
        u1 = UIntBase(3, data)
        u1.Serialize(BinaryWriter(stream))
        self.assertEqual(stream.getvalue(), data)

    def test_deserialize(self):
        u1 = UIntBase(2)
        self.assertEqual(hash(u1), 0)

        # deserialize from stream now. hash should equal hash of b'ab',
        # because size was set to 2.
        u1.Deserialize(BinaryReader(BytesIO(b'abc')))
        self.assertEqual(hash(u1), 25185)

    def test_toarray(self):
        data = b'abc'
        u1 = UIntBase(3, data)
        self.assertEqual(u1.ToArray(), data)

    def test_str(self):
        u1 = UIntBase(3, b'abc')
        self.assertEqual(str(u1), '636261')

    def test_tostring(self):
        u1 = UIntBase(3, b'abc')
        self.assertEqual(u1.ToString(), '636261')

    def test_tostring2(self):
        u1 = UIntBase(3, b'abc')
        self.assertEqual(u1.ToString2(), '616263')

    def test_tobytes(self):
        u1 = UIntBase(3, b'abc')
        self.assertEqual(u1.ToBytes(), b'636261')

    def test_eq(self):
        u1 = UIntBase(3, b'abc')

        # Should equal
        self.assertEqual(u1, u1)
        self.assertEqual(u1, UIntBase(3, b'abc'))
        self.assertEqual(u1, UIntBase(3, bytearray(b'abc')))

        # Should not equal
        self.assertNotEqual(u1, None)
        self.assertNotEqual(u1, 123)
        self.assertNotEqual(u1, 'abc')
        self.assertNotEqual(u1, UIntBase(3, b'abd'))

    def test_compareto_valid(self):
        u1 = UInt160(b'12345678901234567890')

        # Same value should return 0
        u2 = UIntBase(20, b'12345678901234567890')
        self.assertEqual(u1.CompareTo(u2), 0)

        # Higher digit in 'other' should return -1
        u2 = UIntBase(20, b'12345678901234567891')
        self.assertEqual(u1.CompareTo(u2), -1)

        # Lower digit in 'other' should return 1
        u2 = UIntBase(20, b'12345678901234567980')
        self.assertEqual(u1.CompareTo(u2), 1)

        # CompareTo across different UIntBase subclasses
        data = b'12345678901234567890'
        self.assertEqual(UInt160(data).CompareTo(UIntBase(len(data), data)), 0)
        self.assertEqual(UIntBase(len(data), data).CompareTo(UInt160(data)), 0)

        data = b'12345678901234567890123456789012'
        self.assertEqual(UInt256(data).CompareTo(UIntBase(len(data), data)), 0)
        self.assertEqual(UIntBase(len(data), data).CompareTo(UInt256(data)), 0)

    def test_compareto_invalid_datatype(self):
        u1 = UIntBase(20, b'12345678901234567890')

        with self.assertRaises(Exception):
            self.assertEqual(u1.CompareTo('asd'), 0)

        with self.assertRaises(Exception):
            self.assertEqual(u1.CompareTo(b'asd'), 0)

        with self.assertRaises(Exception):
            self.assertEqual(u1.CompareTo(123), 0)

        # Cannot compare uints with different lengths
        with self.assertRaises(Exception):
            a = UInt256(b'12345678901234567890123456789012')
            b = UIntBase(20, b'12345678901234567890')
            a.CompareTo(b)

    def test_dunder_methods(self):
        u1 = UInt160(b'12345678901234567890')
        u1b = UIntBase(20, b'12345678901234567890')

        u_larger = UInt160(b'12345678901234567891')
        u_smaller = UInt160(b'12345678901234567880')

        self.assertTrue(u1 < u_larger)
        self.assertTrue(u1 <= u_larger)
        self.assertTrue(u1 <= u1b)
        self.assertTrue(u1 == u1b)
        self.assertTrue(u1b == u1)
        self.assertTrue(u1 >= u1b)
        self.assertTrue(u1 >= u_smaller)
        self.assertTrue(u1 > u_smaller)


class UInt160TestCase(NeoTestCase):
    def test_initialization(self):
        u0 = UInt160()
        self.assertEqual(hash(u0), 0)

        u1 = UInt160(b'12345678901234567890')
        self.assertEqual(hash(u1), 875770417)

    def test_initialization_invalid_length(self):
        with self.assertRaises(Exception):
            u1 = UInt160(b'12345')


class UInt256TestCase(NeoTestCase):
    def test_initialization(self):
        u0 = UInt256()
        self.assertEqual(hash(u0), 0)

        u1 = UInt256(b'12345678901234567890123456789012')
        self.assertEqual(hash(u1), 875770417)

    def test_initialization_invalid(self):
        with self.assertRaises(Exception):
            u1 = UInt256(b'12345')

        with self.assertRaises(Exception):
            u1 = UInt256('12345678901234567890123456789012')
