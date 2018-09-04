from unittest import TestCase
from neocore.BigInteger import BigInteger
from neocore.UInt160 import UInt160
from neocore.IO.BinaryWriter import BinaryWriter
from neo.Core.FunctionCode import FunctionCode
from neo.IO.MemoryStream import StreamManager


class FunctionCodeTestCase(TestCase):

    def test_1(self):

        fn = FunctionCode()

        self.assertEqual(fn.ReturnType, 255)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(255))

        self.assertEqual(fn.ParameterList, [])
        self.assertEqual(fn.HasDynamicInvoke, False)
        self.assertEqual(fn.HasStorage, False)

    def test_2(self):

        fn = FunctionCode(script=b'abcd', param_list=[], return_type='ff')

        self.assertEqual(fn.ReturnType, 255)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(255))

        fn = FunctionCode(script=b'abcd', param_list=[], return_type=b'ff')

        self.assertEqual(fn.ReturnType, 255)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(255))

        fn = FunctionCode(script=b'abcd', param_list=[], return_type=bytearray(b'\xff'))

        self.assertEqual(fn.ReturnType, 255)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(255))

        fn = FunctionCode(script=b'abcd', param_list=[], return_type=255)

        self.assertEqual(fn.ReturnType, 255)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(255))

        fn = FunctionCode(script=b'abcd', param_list=[], return_type='Void')

        self.assertEqual(fn.ReturnType, 255)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(255))

    def test_3(self):

        fn = FunctionCode(script=b'abcd', param_list=[], return_type=0)

        self.assertEqual(fn.ReturnType, 0)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(0))

        fn = FunctionCode(script=b'abcd', param_list=[], return_type=False)

        self.assertEqual(fn.ReturnType, 0)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(0))

        fn = FunctionCode(script=b'abcd', param_list=[], return_type='0')

        self.assertEqual(fn.ReturnType, 0)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(0))

        fn = FunctionCode(script=b'abcd', param_list=[], return_type=b'0')

        self.assertEqual(fn.ReturnType, 0)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(0))

        fn = FunctionCode(script=b'abcd', param_list=[], return_type='Signature')

        self.assertEqual(fn.ReturnType, 0)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(0))

    def test_4(self):

        fn = FunctionCode(script=b'abcd', param_list=[], return_type='Boolean')

        self.assertEqual(fn.ReturnType, 1)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(1))

        fn = FunctionCode(script=b'abcd', param_list=[], return_type=True)

        self.assertEqual(fn.ReturnType, 1)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(1))

        fn = FunctionCode(script=b'abcd', param_list=[], return_type=1)

        self.assertEqual(fn.ReturnType, 1)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(1))

        fn = FunctionCode(script=b'abcd', param_list=[], return_type='1')

        self.assertEqual(fn.ReturnType, 1)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(1))

        fn = FunctionCode(script=b'abcd', param_list=[], return_type=b'1')

        self.assertEqual(fn.ReturnType, 1)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(1))

    def test_5(self):

        fn = FunctionCode(script=b'abcd', param_list=[], return_type='Array')

        self.assertEqual(fn.ReturnType, 16)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(16))

        fn = FunctionCode(script=b'abcd', param_list=[], return_type='10')

        self.assertEqual(fn.ReturnType, 16)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(16))

        fn = FunctionCode(script=b'abcd', param_list=[], return_type=b'10')

        self.assertEqual(fn.ReturnType, 16)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(16))

    def test_6(self):

        fn = FunctionCode(script=b'abcd', param_list=[], return_type='ByteArray')

        self.assertEqual(fn.ReturnType, 5)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(5))

        fn = FunctionCode(script=b'abcd', param_list=[], return_type='05')

        self.assertEqual(fn.ReturnType, 5)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(5))

        fn = FunctionCode(script=b'abcd', param_list=[], return_type=b'05')

        self.assertEqual(fn.ReturnType, 5)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(5))

        fn = FunctionCode(script=b'abcd', param_list=[], return_type=5)

        self.assertEqual(fn.ReturnType, 5)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(5))

        fn = FunctionCode(script=b'abcd', param_list=[], return_type='5')

        self.assertEqual(fn.ReturnType, 5)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(5))

        fn = FunctionCode(script=b'abcd', param_list=[], return_type=b'5')

        self.assertEqual(fn.ReturnType, 5)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(5))

    def test_7(self):

        fn = FunctionCode(script=b'abcd', param_list=[], return_type='String')

        self.assertEqual(fn.ReturnType, 7)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(7))

        fn = FunctionCode(script=b'abcd', param_list=[], return_type='7')

        self.assertEqual(fn.ReturnType, 7)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(7))

        fn = FunctionCode(script=b'abcd', param_list=[], return_type=b'07')

        self.assertEqual(fn.ReturnType, 7)
        self.assertEqual(fn.ReturnTypeBigInteger, BigInteger(7))
