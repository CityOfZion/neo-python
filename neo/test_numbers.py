from neo.Utils.NeoTestCase import NeoTestCase
from neo.Fixed8 import Fixed8
from neo.BigInteger import BigInteger


class FancyNumberTestCase(NeoTestCase):


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
        