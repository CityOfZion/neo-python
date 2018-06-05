import binascii
import base58
from mock import patch
from neo.Utils.NeoTestCase import NeoTestCase
from neocore.KeyPair import KeyPair


class ConstructorTestCase(NeoTestCase):
    def test_wrong_private_key_length(self):
        priv_key = b'\xDE\xAD\xBE\xEF'
        with self.assertRaises(ValueError) as context:
            KeyPair(priv_key)
        self.assertEqual('Invalid private key', str(context.exception))

    @patch('neocore.KeyPair.bitcoin.privkey_to_pubkey')
    def test_fail_to_determine_plublic_key(self, patched_priv_to_pubkey):
        # https://github.com/vbuterin/pybitcointools/blob/aeb0a2bbb8bbfe421432d776c649650eaeb882a5/bitcoin/main.py#L291
        patched_priv_to_pubkey.side_effect = Exception("Invalid privkey")

        with self.assertRaises(Exception) as context:

            KeyPair(bytes(32 * 'A', 'utf8'))
        self.assertEqual('Could not determine public key', str(context.exception))


class PrivateKeyFromWIFTestCase(NeoTestCase):
    def test_should_throw_error_on_too_short_wif(self):
        with self.assertRaises(ValueError) as context:
            KeyPair.PrivateKeyFromWIF('brokenwif')

        self.assertIn('Please provide a wif with a length of 52 bytes', str(context.exception))

    def test_should_throw_error_on_invalid_wif(self):
        with self.assertRaises(ValueError) as context:
            KeyPair.PrivateKeyFromWIF(52 * 'A')

        self.assertEqual('Invalid format!', str(context.exception))

    def test_should_throw_error_on_invalid_checksum(self):
        # build fake wif
        fakewif = bytearray(34 * 'A', 'utf8')
        fakewif[0] = 0x80
        fakewif[33] = 0x01
        # fake checksum
        fakewif.append(0xDE)
        fakewif.append(0xAD)
        fakewif.append(0xBE)
        fakewif.append(0xEF)

        encodedFakeWIF = base58.b58encode(bytes(fakewif))

        with self.assertRaises(ValueError) as context:
            KeyPair.PrivateKeyFromWIF(encodedFakeWIF)

        self.assertEqual('Invalid WIF Checksum!', str(context.exception))

    def test_should_work(self):
        privkey = KeyPair.PrivateKeyFromWIF("L44B5gGEpqEDRS9vVPz7QT35jcBG2r3CZwSwQ4fCewXAhAhqGVpP")
        self.assertEqual(binascii.hexlify(privkey), b"cbf4b9f70470856bb4f40f80b87edb90865997ffee6df315ab166d713af433a5")


class PrivateKeyFromNEP2TestCase(NeoTestCase):
    def test_should_throw_error_on_too_short_nep2_key(self):
        with self.assertRaises(ValueError) as context:
            KeyPair.PrivateKeyFromNEP2('invalid', 'pwd')

        self.assertIn('Please provide a nep2_key with a length of 58 bytes', str(context.exception))

    def test_should_throw_error_on_invalid_nep2_key(self):
        with self.assertRaises(ValueError) as context:
            KeyPair.PrivateKeyFromNEP2(58 * 'A', 'pwd')

        self.assertEqual('Invalid nep2_key', str(context.exception))

    def test_should_work(self):
        nep2_key = "6PYVPVe1fQznphjbUxXP9KZJqPMVnVwCx5s5pr5axRJ8uHkMtZg97eT5kL"
        pwd = "TestingOneTwoThree"
        should_equal_private_key = b"cbf4b9f70470856bb4f40f80b87edb90865997ffee6df315ab166d713af433a5"
        privkey = KeyPair.PrivateKeyFromNEP2(nep2_key, pwd)
        privkey_hex = binascii.hexlify(privkey)
        self.assertEqual(privkey_hex, should_equal_private_key)

    def test_should_throw_error_on_invalid_password(self):
        nep2_key = "6PYVPVe1fQznphjbUxXP9KZJqPMVnVwCx5s5pr5axRJ8uHkMtZg97eT5kL"
        pwd = "invalid-pwd"
        with self.assertRaises(ValueError) as context:
            KeyPair.PrivateKeyFromNEP2(nep2_key, pwd)

        self.assertEqual('Wrong passphrase', str(context.exception))


class GetAddressTestCase(NeoTestCase):
    def test_should_return_valid_address(self):
        kp = KeyPair(binascii.unhexlify("cbf4b9f70470856bb4f40f80b87edb90865997ffee6df315ab166d713af433a5"))
        self.assertEqual(kp.GetAddress(), "AStZHy8E6StCqYQbzMqi4poH7YNDHQKxvt")


class ExportNEP2TestCase(NeoTestCase):
    def test_should_throw_error_on_too_short_passphrase(self):
        kp = KeyPair(binascii.unhexlify("cbf4b9f70470856bb4f40f80b87edb90865997ffee6df315ab166d713af433a5"))
        with self.assertRaises(ValueError) as context:
            kp.ExportNEP2("x")

        self.assertIn('Passphrase must have a minimum', str(context.exception))

    def test_should_export_valid_nep2_key(self):
        kp = KeyPair(binascii.unhexlify("cbf4b9f70470856bb4f40f80b87edb90865997ffee6df315ab166d713af433a5"))
        nep2_key = kp.ExportNEP2("TestingOneTwoThree")
        self.assertEqual(nep2_key, "6PYVPVe1fQznphjbUxXP9KZJqPMVnVwCx5s5pr5axRJ8uHkMtZg97eT5kL")

    def test_should_export_valid_nep2_key_with_emoji_pwd(self):
        pwd = "hellö♥️"
        privkey = "03eb20a711f93c04459000c62cc235f9e9da82382206b812b07fd2f81779aa42"

        # expected outputs
        target_address = "AXQUduANGZF4e7wDazVAtyRLHwMounaUMA"
        target_encrypted_key = "6PYWdv8bP9vbfGsNnjzDawCoXCYpk4rnWG8xTZrvdzx6FjB6jv4H9MM586"

        kp = KeyPair(binascii.unhexlify(privkey))
        nep2_key = kp.ExportNEP2(pwd)
        self.assertEqual(nep2_key, target_encrypted_key)
        self.assertEqual(kp.GetAddress(), target_address)


class ExportWIFTestCase(NeoTestCase):
    def test_should_export_valid_wif_key(self):
        kp = KeyPair(binascii.unhexlify("cbf4b9f70470856bb4f40f80b87edb90865997ffee6df315ab166d713af433a5"))
        wif = kp.Export()
        self.assertEqual(wif, "L44B5gGEpqEDRS9vVPz7QT35jcBG2r3CZwSwQ4fCewXAhAhqGVpP")
