import binascii
import base58
from mock import patch
from neo.Utils.NeoTestCase import NeoTestCase
from neo.Wallets.KeyPair import KeyPair


class ConstructorTestCase(NeoTestCase):
    def test_wrong_private_key_length(self):
        priv_key = b'\xDE\xAD\xBE\xEF'
        with self.assertRaises(ValueError) as context:
            KeyPair(priv_key)
        self.assertEqual('Invalid private key', str(context.exception))

    @patch('neo.Wallets.KeyPair.bitcoin.privkey_to_pubkey')
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
