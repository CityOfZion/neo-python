from neo.Utils.NeoTestCase import NeoTestCase
from neo.Wallets.KeyPair import KeyPair
import binascii

class WalletTestCase(NeoTestCase):


    testnet_addr = 'AdMDZGto3xWozB1HSjjVv27RL3zUM8LzpV'

    testnet_WIF = 'L3MBUkKU5kYg16KSZnqcaTj2pG5ei3fN9A4X7rxXys18GBDa3bH8'
    testnet_prikey = b'\xb6\xde\x16\xf4\xe2\x93\x90\xeb\xaf\xbc\x9fY1\r\x06\x08C\x86\xcc/+\xa0\xcb\xc6\x1f\xf3\xe9\x86\x97\x92\xd4\x0b'

#    testnet_pub_key = b'03f3a3b5a4d873933fc7f4b53113e8eb999fb20038271fbbb10255585670c3c312'
    testnet_pub_key = b'039c1c452e0f8133723e2b015105448c30dcb0f37cfc967437704e3d63bd1d2115'

    testnet_pub_keyhash = '2321bde5302eda01c0dfd8e0a3828dbf00e9fcf2'

    def test_key_pair(self):


        pk_from_wif = KeyPair.PrivateKeyFromWIF(self.testnet_WIF)

        self.assertEqual(pk_from_wif, self.testnet_prikey)

        kp = KeyPair(priv_key=pk_from_wif)


        self.assertEqual(kp.PublicKey.encode_point(True), self.testnet_pub_key)
#        self.assertEqual(kp.PublicKeyHash.ToString(), self.testnet_pub_keyhash)


        export_wif = kp.Export()

        self.assertEqual(export_wif, self.testnet_WIF)


    kp2_pub = '036417b92ec52f100a1003fe79b9b163aebf812dee26e31a2d6b767b661f0ed2d0'
    kp2_wif = 'KxtFy754kJc2KK5SWPR8UwfeXiRkXiQhNzk4pDoqBt17f5WSTt3D'

    def test_kp2(self):
        pk_from_wif = KeyPair.PrivateKeyFromWIF(self.kp2_wif)

        print("pk from wif %s " % pk_from_wif)

        kp = KeyPair(priv_key=pk_from_wif)

        print("kp pubkey %s " % kp.PublicKey.encode_point(True))