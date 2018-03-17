from unittest import TestCase
from neo.VM.InteropService import *


class InteropTest(TestCase):

    def test_map1(self):

        map = Map()

        self.assertEqual(map.Keys, [])
        self.assertEqual(map.Values, [])

        map.SetItem(Integer(BigInteger(3)), ByteArray(b'abc'))

        self.assertEqual(map.Keys, [Integer(BigInteger(3))])

        self.assertEqual(map.Values, [ByteArray(b'abc')])

    def test_map2(self):

        map = Map({'a': 1, 'b': 2, 'c': 3})

        self.assertEqual(map.Count, 3)

        self.assertEqual(map.ContainsKey('a'), True)

        self.assertEqual(map.Contains('a'), False)

        map.Clear()

        self.assertEqual(map.GetMap(), {})

    def test_map3(self):

        map = Map({'a': 1, 'b': 2, 'c': 3})

        self.assertEqual(map.GetBoolean(), True)

        with self.assertRaises(Exception) as context:
            map.GetByteArray()

        with self.assertRaises(Exception) as context:
            map.GetBigInteger()

        map2 = Map({'a': 1, 'b': 2, 'c': 3})

        self.assertEqual(map, map2)

        self.assertTrue(map.Remove('a'), True)

        self.assertEqual(map.Count, 2)

        self.assertNotEqual(map, map2)

        self.assertEqual(map.TryGetValue('b'), (True, 2))

        self.assertEqual(map.TryGetValue('h'), (False, None))

        map.SetItem('h', 9)

        self.assertEqual(map.GetItem('h'), 9)

        self.assertEqual(map.GetMap(), {'b': 2, 'c': 3, 'h': 9})
