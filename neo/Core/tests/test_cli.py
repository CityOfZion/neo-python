from unittest import TestCase
from neo.Core.bin import cli
import subprocess
import warnings
import neo


class CliTestCase(TestCase):
    def test_address_to_scripthash(self):
        address = "AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y"
        scripthash = cli.address_to_scripthash(address)
        self.assertEqual(scripthash, b'#\xba\'\x03\xc52c\xe8\xd6\xe5"\xdc2 39\xdc\xd8\xee\xe9')

        address = "AK2nJJpJr6o664CWJKi1QRXjqeic2zRpxx"
        with self.assertRaises(cli.ConversionError):
            scripthash = cli.address_to_scripthash(address)

    def test_scripthash_to_address(self):
        scripthash = "0xe9eed8dc39332032dc22e5d6e86332c50327ba23"
        address = cli.scripthash_to_address(scripthash)
        self.assertEqual(address, "AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y")

        scripthash = "23ba2703c53263e8d6e522dc32203339dcd8eee9"
        address = cli.scripthash_to_address(scripthash)
        self.assertEqual(address, "AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y")

        scripthash = "0xe9eed8dc39332032dc22e5d6e86332c50327baxx"
        with self.assertRaises(cli.ConversionError):
            address = cli.scripthash_to_address(scripthash)

    def test_create_wallet(self):
        wallet = cli.create_wallet()
        self.assertIn("private_key", wallet)
        self.assertIn("address", wallet)
        self.assertIsInstance(wallet["private_key"], str)
        self.assertIsInstance(wallet["address"], str)

    def test_main(self):
        warnings.filterwarnings('ignore', category=ResourceWarning)  # filters warnings about subprocess files still being open

        version = subprocess.Popen(['np-utils', '--version'], stdout=subprocess.PIPE)
        self.assertIn(neo.__version__, version.stdout.read().decode('utf-8'))

        address_to_scripthash = subprocess.Popen(['np-utils', '--address-to-scripthash', 'AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y'], stdout=subprocess.PIPE)
        self.assertEqual(
            b'Scripthash big endian:  0xe9eed8dc39332032dc22e5d6e86332c50327ba23\nScripthash little endian: 23ba2703c53263e8d6e522dc32203339dcd8eee9\nScripthash neo-python format: b\'#\\xba\\\'\\x03\\xc52c\\xe8\\xd6\\xe5"\\xdc2 39\\xdc\\xd8\\xee\\xe9\'\n',
            address_to_scripthash.stdout.read())

        scripthash_to_address = subprocess.Popen(['np-utils', '--scripthash-to-address', "0xe9eed8dc39332032dc22e5d6e86332c50327ba23"], stdout=subprocess.PIPE)
        self.assertIn("AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y", scripthash_to_address.stdout.read().decode('utf-8'))

        wallet1 = subprocess.Popen(['np-utils', '--create-wallet'], stdout=subprocess.PIPE)
        self.assertIn("private_key", wallet1.stdout.read().decode('utf-8'))

        wallet2 = subprocess.Popen(['np-utils', '--create-wallet'], stdout=subprocess.PIPE)
        self.assertIn("address", wallet2.stdout.read().decode('utf-8'))

        print_help = subprocess.Popen(['np-utils', '--h'], stdout=subprocess.PIPE)
        self.assertIn("help", print_help.stdout.read().decode('utf-8'))
