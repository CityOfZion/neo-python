from unittest import TestCase
from neo.VM.InteropService import ByteArray, Integer, BigInteger, Boolean
from neo.SmartContract.ContractParameter import ContractParameter
from neo.SmartContract.ContractParameterType import ContractParameterType
from neocore.UInt256 import UInt256
from neocore.UInt160 import UInt160
from neocore.Cryptography.ECCurve import EllipticCurve


class EventTestCase(TestCase):

    def test_from_json(self):

        jsn = {
            'type': str(ContractParameterType.String),
            'value': 'hello'
        }
        cp = ContractParameter.FromJson(jsn)
        cpj = cp.ToJson()
        self.assertEqual(cpj, jsn)

        self.assertEqual(cp.Type, ContractParameterType.String)
        self.assertEqual(cp.Value, 'hello')

        # the following test ensures the type can be an int
        jsn = {
            'type': 7,
            'value': 'hi'
        }
        cp = ContractParameter.FromJson(jsn)

        self.assertEqual(cp.Type, ContractParameterType.String)
        self.assertEqual(cp.Value, 'hi')

        # the following test ensures the type can be a string containing an int
        jsn = {
            'type': '7',
            'value': 'goodbye'
        }
        cp = ContractParameter.FromJson(jsn)

        self.assertEqual(cp.Type, ContractParameterType.String)
        self.assertEqual(cp.Value, 'goodbye')

        # the following test ensures the type can be a string of the type literal
        jsn = {
            'type': 'String',
            'value': 'bye'
        }
        cp = ContractParameter.FromJson(jsn)

        self.assertEqual(cp.Type, ContractParameterType.String)
        self.assertEqual(cp.Value, 'bye')

        jsn = {
            'type': str(ContractParameterType.Integer),
            'value': 2003
        }

        cp = ContractParameter.FromJson(jsn)
        self.assertEqual(cp.Type, ContractParameterType.Integer)
        self.assertEqual(cp.Value, 2003)
        self.assertEqual(cp.ToJson(), jsn)

        jsn = {
            'type': str(ContractParameterType.Hash160),
            'value': 'd7678dd97c000be3f33e9362e673101bac4ca654'
        }

        cp = ContractParameter.FromJson(jsn)
        self.assertEqual(cp.Type, ContractParameterType.Hash160)
        self.assertIsInstance(cp.Value, UInt160)
        self.assertEqual(cp.Value.ToString(), 'd7678dd97c000be3f33e9362e673101bac4ca654')
        self.assertEqual(cp.ToJson(), jsn)

        jsn = {
            'type': str(ContractParameterType.Hash256),
            'value': 'cedb5c4e24b1f6fc5b239f2d1049c3229ad5ed05293c696b3740dc236c3f41b4'
        }

        cp = ContractParameter.FromJson(jsn)
        self.assertEqual(cp.Type, ContractParameterType.Hash256)
        self.assertIsInstance(cp.Value, UInt256)
        self.assertEqual(cp.Value.ToString(), 'cedb5c4e24b1f6fc5b239f2d1049c3229ad5ed05293c696b3740dc236c3f41b4')
        self.assertEqual(cp.ToJson(), jsn)

        jsn = {
            'type': str(ContractParameterType.PublicKey),
            'value': '0327da12b5c40200e9f65569476bbff2218da4f32548ff43b6387ec1416a231ee8'
        }

        cp = ContractParameter.FromJson(jsn)
        self.assertEqual(cp.Type, ContractParameterType.PublicKey)
        self.assertIsInstance(cp.Value, EllipticCurve.ECPoint)

        jsn = {
            'type': str(ContractParameterType.ByteArray),
            'value': bytearray(b'\x00\x01\x02').hex()
        }

        cp = ContractParameter.FromJson(jsn)
        self.assertEqual(cp.Type, ContractParameterType.ByteArray)
        self.assertEqual(len(cp.Value), 3)
        self.assertEqual(cp.Value, bytearray(b'\x00\x01\x02'))
        self.assertEqual(cp.ToJson(), jsn)

        jsn = {
            'type': str(ContractParameterType.Boolean),
            'value': 0
        }
        cp = ContractParameter.FromJson(jsn)
        self.assertEqual(cp.Type, ContractParameterType.Boolean)
        self.assertEqual(cp.Value, False)

        jsn = {
            'type': str(ContractParameterType.Boolean),
            'value': 1
        }
        cp = ContractParameter.FromJson(jsn)
        self.assertEqual(cp.Type, ContractParameterType.Boolean)
        self.assertEqual(cp.Value, True)

        jsn = {
            'type': str(ContractParameterType.Boolean),
            'value': True
        }
        cp = ContractParameter.FromJson(jsn)
        self.assertEqual(cp.Type, ContractParameterType.Boolean)
        self.assertEqual(cp.Value, True)
        self.assertEqual(cp.ToJson(), jsn)

        jsn = {
            'type': str(ContractParameterType.Boolean),
            'value': False
        }
        cp = ContractParameter.FromJson(jsn)
        self.assertEqual(cp.Type, ContractParameterType.Boolean)
        self.assertEqual(cp.Value, False)
        self.assertEqual(cp.ToJson(), jsn)

        jsn = {
            'type': str(ContractParameterType.Array),
            'value': [
                {
                    'type': str(ContractParameterType.Boolean),
                    'value': 0
                }, {
                    'type': str(ContractParameterType.ByteArray),
                    'value': bytearray(b'\x00\x01\x02').hex()
                }, {
                    'type': str(ContractParameterType.Hash256),
                    'value': 'cedb5c4e24b1f6fc5b239f2d1049c3229ad5ed05293c696b3740dc236c3f41b4'
                }
            ]
        }

        cp = ContractParameter.FromJson(jsn)
        self.assertEqual(cp.Type, ContractParameterType.Array)
        self.assertIsInstance(cp.Value, list)

        self.assertEqual(cp.Value[0].Value, False)
        self.assertEqual(cp.Value[1].Value, bytearray(b'\x00\x01\x02'))
        self.assertIsInstance(cp.Value[2].Value, UInt256)

        self.assertEqual(cp.ToJson(), jsn)

    def test_to_parameter(self):

        stack_item = Integer(BigInteger(14))

        cp1 = ContractParameter.AsParameterType(ContractParameterType.Integer, stack_item)
        self.assertEqual(cp1.ToJson(), {'type': 'Integer', 'value': 14})

        cp1 = ContractParameter.AsParameterType(ContractParameterType.Boolean, stack_item)
        self.assertEqual(cp1.ToJson(), {'type': 'Boolean', 'value': True})

        cp1 = ContractParameter.AsParameterType(ContractParameterType.ByteArray, stack_item)
        self.assertEqual(cp1.ToJson(), {'type': 'ByteArray', 'value': '0e'})

        with self.assertRaises(Exception) as ctx:
            cp1 = ContractParameter.AsParameterType(ContractParameterType.Array, stack_item)

        cp1 = ContractParameter.AsParameterType(ContractParameterType.String, stack_item)
        self.assertEqual(cp1.ToJson(), {'type': 'String', 'value': '14'})

        cp1 = ContractParameter.AsParameterType(ContractParameterType.InteropInterface, stack_item)
        self.assertEqual(cp1.ToJson(), {'type': 'InteropInterface'})

        stack_item = Boolean(False)

        cp1 = ContractParameter.AsParameterType(ContractParameterType.Integer, stack_item)
        self.assertEqual(cp1.ToJson(), {'type': 'Integer', 'value': 0})

        cp1 = ContractParameter.AsParameterType(ContractParameterType.Boolean, stack_item)
        self.assertEqual(cp1.ToJson(), {'type': 'Boolean', 'value': False})

        cp1 = ContractParameter.AsParameterType(ContractParameterType.ByteArray, stack_item)
        self.assertEqual(cp1.ToJson(), {'type': 'ByteArray', 'value': '00'})

        with self.assertRaises(Exception) as ctx:
            cp1 = ContractParameter.AsParameterType(ContractParameterType.Array, stack_item)

        cp1 = ContractParameter.AsParameterType(ContractParameterType.String, stack_item)
        self.assertEqual(cp1.ToJson(), {'type': 'String', 'value': 'False'})

        cp1 = ContractParameter.AsParameterType(ContractParameterType.InteropInterface, stack_item)
        self.assertEqual(cp1.ToJson(), {'type': 'InteropInterface'})

        stack_item = ByteArray(bytearray(b'\xe0\x02'))

        cp1 = ContractParameter.AsParameterType(ContractParameterType.Integer, stack_item)
        self.assertEqual(cp1.ToJson(), {'type': 'Integer', 'value': 736})

        cp1 = ContractParameter.AsParameterType(ContractParameterType.Boolean, stack_item)
        self.assertEqual(cp1.ToJson(), {'type': 'Boolean', 'value': True})

        cp1 = ContractParameter.AsParameterType(ContractParameterType.ByteArray, stack_item)
        self.assertEqual(cp1.ToJson(), {'type': 'ByteArray', 'value': 'e002'})

        with self.assertRaises(Exception) as ctx:
            cp1 = ContractParameter.AsParameterType(ContractParameterType.Array, stack_item)

        cp1 = ContractParameter.AsParameterType(ContractParameterType.String, stack_item)
        self.assertEqual(cp1.ToJson(), {'type': 'String', 'value': 'e002'})

        cp1 = ContractParameter.AsParameterType(ContractParameterType.InteropInterface, stack_item)
        self.assertEqual(cp1.ToJson(), {'type': 'InteropInterface'})
