from neo.Utils.NeoTestCase import NeoTestCase
from neo.Wallets.utils import to_aes_key
from neocore.KeyPair import KeyPair
from neocore.UInt160 import UInt160
from neo.SmartContract.Contract import Contract
import binascii
from neocore.Cryptography.Crypto import Crypto
import hashlib

from neo.Wallets.Wallet import Wallet


class WalletTestCase(NeoTestCase):

    iv = b'x\xdb\xa9\xc8\xd8\xb6\x80A\xf3Y\xb4:\x8b\xf03\xf1'
    mk = b'k\xcc\xf3\xb6\x94\x16\xc8\x86\xc2\xd5\xc6\xdam\xd8^D\x87c\x17\xd7G\xb8w\x86 \xffD\xac\x80X\xf0\xa3'
    pk = b'p\x8a/d\xd7\xcc\xeedr\x91\xd1^3{\x9d"8/\x82H\xb6\x9bu\xeb\xe6\x84\xe6f\xb0m\x12&'

    contract_script = b"!\x02\xaf\xd5\xd8\x0f5\xd6'\xb9'\x16\xd6\xf5\xc7\xdb\x88\xea\xc7Ib\x10\xd5Zrg\xdf\xb6\xbeC\xe3\xa0\x01`\xac"

    contract_script_hash = b"b3c77e64a4c1188cfcf3ac6e97c6892a647dc440"
    contract_address = 'AMgLH8JnE1PCoG4xwKdHxpCJ2Pa3Pn9BeN'

    pubkeyhash = b'fcd1112b4490ead1d993315e41c32a4e86077b3c'
    pubkey_encoded = b'02afd5d80f35d627b92716d6f5c7db88eac7496210d55a7267dfb6be43e3a00160'
    pubkey_not_comp = b'04afd5d80f35d627b92716d6f5c7db88eac7496210d55a7267dfb6be43e3a00160b4ebcd81a3f173a9cf32c82f72f2f2e8890c22d00a576573971706b8a58e6a5e'
    pubkey_not_comp_b = b'\x04\xaf\xd5\xd8\x0f5\xd6\'\xb9\'\x16\xd6\xf5\xc7\xdb\x88\xea\xc7Ib\x10\xd5Zrg\xdf\xb6\xbeC\xe3\xa0\x01`\xb4\xeb\xcd\x81\xa3\xf1s\xa9\xcf2\xc8/r\xf2\xf2\xe8\x89\x0c"\xd0\nWes\x97\x17\x06\xb8\xa5\x8ej^'

    pubkey_x = 79532578114149170381626880618597693941185535309037206278631029726225448829280
    pubkey_y = 81832940158310313407998577722079876882736317001913195964672591118898574551646

    wif = 'KzzURAp1mKdWVFRbTU2ydFqPznnUqNnU4mKLPGLnJARqqKzDCvNF'

    decrypted_pk = b'\xaf\xd5\xd8\x0f5\xd6\'\xb9\'\x16\xd6\xf5\xc7\xdb\x88\xea\xc7Ib\x10\xd5Zrg\xdf\xb6\xbeC\xe3\xa0\x01`\xb4\xeb\xcd\x81\xa3\xf1s\xa9\xcf2\xc8/r\xf2\xf2\xe8\x89\x0c"\xd0\nWes\x97\x17\x06\xb8\xa5\x8ej^p\x8a/d\xd7\xcc\xeedr\x91\xd1^3{\x9d"8/\x82H\xb6\x9bu\xeb\xe6\x84\xe6f\xb0m\x12&'

    def test_a(self):

        key = KeyPair(priv_key=self.pk)

        self.assertEqual(key.PublicKey.x, self.pubkey_x)
        self.assertEqual(key.PublicKey.y, self.pubkey_y)

        self.assertEqual(key.PublicKey.encode_point(True), self.pubkey_encoded)
        self.assertEqual(key.PublicKey.encode_point(False), self.pubkey_not_comp)

        self.assertIsInstance(key.PublicKeyHash, UInt160)

        self.assertEqual(key.PublicKeyHash.ToBytes(), self.pubkeyhash)
        self.assertEqual(key.Export(), self.wif)

        private_key_from_wif = KeyPair.PrivateKeyFromWIF(self.wif)

        self.assertEqual(private_key_from_wif, self.pk)

    def test_b(self):

        key = KeyPair(priv_key=self.pk)

        contract = Contract.CreateSignatureContract(key.PublicKey)

        self.assertEqual(binascii.unhexlify(contract.Script), self.contract_script)
        self.assertEqual(contract.ScriptHash.ToBytes(), self.contract_script_hash)

        self.assertEqual(contract.Address, self.contract_address)

        self.assertEqual(contract.PublicKeyHash, key.PublicKeyHash)
        self.assertEqual(contract.PublicKeyHash.ToBytes(), self.pubkeyhash)

    def test_c(self):

        key = KeyPair(priv_key=self.decrypted_pk)

        self.assertEqual(key.PublicKey.x, self.pubkey_x)
        self.assertEqual(key.PublicKey.y, self.pubkey_y)

        self.assertEqual(key.PublicKey.encode_point(True), self.pubkey_encoded)
        self.assertEqual(key.PublicKey.encode_point(False), self.pubkey_not_comp)

        self.assertIsInstance(key.PublicKeyHash, UInt160)

        self.assertEqual(key.PublicKeyHash.ToBytes(), self.pubkeyhash)
        self.assertEqual(key.Export(), self.wif)

        private_key_from_wif = KeyPair.PrivateKeyFromWIF(self.wif)

        self.assertEqual(private_key_from_wif, self.pk)

    mpk = b'\xd5\x8e\xc1J\xd7>\x01Y\x7f\xda5\x14gH<+\xddv\x19\xc0\xe3\xa2\xd0OT\xae\xf0b`\xb6\x17g'

    nmsg = b'8000000192133b63f9da5c7a675ca1293beb15723809a29cdf0d7bad309e7b07e4fddf8a0100029b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f50500000000010ced78d6aacc45c758b723411b5fd713988c349b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500bbeea00000000049bc7ccb4e65a90d6067d8b171d66db0eab70d9d'
    nmpk = mpk

    neon_sig = 'ea0b16eacce905984ca82852d40030f6bf3f5440bf06c0b632043de9b2a95b8f3ea497c2d7702aad5be5c7463610ee58eb92ba6c39d6e86affd5cb7dec028ee9'

    hashhex = '18b7bfca2a4a81ae72f4ad766a6f7aded1c7155118e3679d1b37a2d66d92bd77'

    def test_neon_sig(self):

        key = KeyPair(priv_key=self.nmpk)

        hhex = hashlib.sha256(binascii.unhexlify(self.nmsg)).hexdigest()

        self.assertEqual(hhex, self.hashhex)

        sig = Crypto.Sign(self.nmsg, key.PrivateKey)

        self.assertEqual(sig.hex(), self.neon_sig)

    def test_get_contains_key_should_be_found(self):
        wallet = Wallet("fakepath", to_aes_key("123"), True)
        wallet.CreateKey()
        keypair = wallet.GetKeys()[0]
        self.assertTrue(wallet.ContainsKey(keypair.PublicKey))

    def test_get_contains_key_should_not_be_found(self):
        wallet = Wallet("fakepath", to_aes_key("123"), True)
        wallet.CreateKey()
        keypair = KeyPair(priv_key=self.pk)
        self.assertFalse(wallet.ContainsKey(keypair.PublicKey))
