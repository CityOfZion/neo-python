from neo.Utils.NeoTestCase import NeoTestCase
from neo.Network.address import Address
from datetime import datetime


class AddressTest(NeoTestCase):
    def test_init_simple(self):
        host = '127.0.0.1:80'
        a = Address(host)
        self.assertEqual(0, a.last_connection)
        self.assertEqual(a.address, host)

        # test custom 'last_connection_to'
        b = Address(host, 123)
        self.assertEqual(123, b.last_connection)

    def test_now_helper(self):
        n = Address.Now()
        delta = datetime.now().utcnow().timestamp() - n
        self.assertTrue(delta < 2)

    def test_equality(self):
        """
        Only the host:port matters in equality
        """
        a = Address('127.0.0.1:80', last_connection_to=0)
        b = Address('127.0.0.1:80', last_connection_to=0)
        c = Address('127.0.0.1:99', last_connection_to=0)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

        # last connected does not influence equality
        b.last_connection = 123
        self.assertEqual(a, b)

        # different port does change equality
        b.address = "127.0.0.1:99"
        self.assertNotEqual(a, b)

        # test diff types
        self.assertNotEqual(int(1), a)
        self.assertNotEqual("127.0.0.1:80", a)

    def test_repr_and_str(self):
        host = '127.0.0.1:80'
        a = Address(host, last_connection_to=0)
        self.assertEqual(host, str(a))

        x = repr(a)
        self.assertIn("Address", x)
        self.assertIn(host, x)

    def test_split(self):
        a = Address('127.0.0.1:80')
        host, port = a.split(':')
        self.assertEqual(host, '127.0.0.1')
        self.assertEqual(port, '80')

        host, port = a.rsplit(':', maxsplit=1)
        self.assertEqual(host, '127.0.0.1')
        self.assertEqual(port, '80')

    def test_str_formatting(self):
        a = Address('127.0.0.1:80')
        expected = "   127.0.0.1:80"
        out = f"{a:>15}"
        self.assertEqual(expected, out)

    def test_list_lookup(self):
        a = Address('127.0.0.1:80')
        b = Address('127.0.0.2:80')
        c = Address('127.0.0.1:80')
        d = Address('127.0.0.1:99')

        z = [a, b]
        self.assertTrue(a in z)
        self.assertTrue(b in z)
        # duplicate check, equals to 'a'
        self.assertTrue(c in z)
        self.assertFalse(d in z)

    def test_dictionary_lookup(self):
        """for __hash__"""
        a = Address('127.0.0.1:80')
        b = Address('127.0.0.2:80')
        addr = {a: 1, b: 2}
        self.assertEqual(addr[a], 1)
        self.assertEqual(addr[b], 2)
