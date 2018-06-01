from unittest import TestCase
from neo.Prompt import Utils
from neocore.Fixed8 import Fixed8
from neocore.UInt160 import UInt160


class TestInputParser(TestCase):

    def test_utils_1(self):

        args = [1, 2, 3]

        args, neo, gas = Utils.get_asset_attachments(args)

        self.assertEqual(args, [1, 2, 3])
        self.assertIsNone(neo)
        self.assertIsNone(gas)

    def test_utils_2(self):

        args = []

        args, neo, gas = Utils.get_asset_attachments(args)

        self.assertEqual(args, [])
        self.assertIsNone(neo)
        self.assertIsNone(gas)

    def test_utils_3(self):

        args = None

        with self.assertRaises(Exception):
            Utils.get_asset_attachments(args)

    def test_utils_4(self):

        args = [1, 2, '--attach-neo=100']

        args, neo, gas = Utils.get_asset_attachments(args)

        self.assertEqual(args, [1, 2])
        self.assertEqual(neo, Fixed8.FromDecimal(100))
        self.assertIsNone(gas)

    def test_utils_5(self):
        args = [1, 2, '--attach-gas=100.0003']

        args, neo, gas = Utils.get_asset_attachments(args)

        self.assertEqual(args, [1, 2])
        self.assertEqual(gas, Fixed8.FromDecimal(100.0003))
        self.assertIsNone(neo)

    def test_utils_6(self):
        args = [1, 2, '--attachgas=100.0003']

        args, neo, gas = Utils.get_asset_attachments(args)

        self.assertEqual(args, [1, 2, '--attachgas=100.0003'])
        self.assertIsNone(neo)
        self.assertIsNone(gas)

    def test_utils_7(self):
        args = [1, 2, '--attach-gas=100.0003', '--attach-neo=5.7']

        args, neo, gas = Utils.get_asset_attachments(args)

        self.assertEqual(args, [1, 2])
        self.assertEqual(neo, None)
        self.assertEqual(gas, Fixed8.FromDecimal(100.0003))

    def test_utils_8(self):
        args = [1, 2, '--attach-gas=100.0003', '--attach-neo=6']

        args, neo, gas = Utils.get_asset_attachments(args)

        self.assertEqual(args, [1, 2])
        self.assertEqual(neo, Fixed8.FromDecimal(6))
        self.assertEqual(gas, Fixed8.FromDecimal(100.0003))

    def test_owner_1(self):
        args = [1, 2]

        args, owners = Utils.get_owners_from_params(args)

        self.assertEqual(args, [1, 2])
        self.assertIsNone(owners)

    def test_owner_2(self):
        args = [1, 2, "--owners=['ABC','DEF',]"]

        args, owners = Utils.get_owners_from_params(args)

        self.assertEqual(args, [1, 2])
        self.assertEqual(owners, set())

    def test_owner_3(self):
        args = [1, 2, "--owners=['APRgMZHZubii29UXF9uFa6sohrsYupNAvx','AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK',]"]

        args, owners = Utils.get_owners_from_params(args)

        self.assertEqual(args, [1, 2])
        self.assertEqual(len(owners), 2)

        self.assertIsInstance(list(owners)[0], UInt160)

    def test_owner_and_assets(self):

        args = [1, 2, "--owners=['APRgMZHZubii29UXF9uFa6sohrsYupNAvx','AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK',]", '--attach-neo=10']

        args, owners = Utils.get_owners_from_params(args)

        args, neo, gas = Utils.get_asset_attachments(args)

        self.assertEqual(args, [1, 2])
        self.assertEqual(len(owners), 2)

        self.assertIsInstance(list(owners)[0], UInt160)

        self.assertEqual(neo, Fixed8.FromDecimal(10))
