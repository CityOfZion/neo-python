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
        return

        pk_from_wif = KeyPair.PrivateKeyFromWIF(self.testnet_WIF)

        self.assertEqual(pk_from_wif, self.testnet_prikey)

        kp = KeyPair(priv_key=pk_from_wif)


        self.assertEqual(kp.PublicKey.encode_point(True), self.testnet_pub_key)


        export_wif = kp.Export()

        self.assertEqual(export_wif, self.testnet_WIF)


    kp2_pub = '036417b92ec52f100a1003fe79b9b163aebf812dee26e31a2d6b767b661f0ed2d0'
    kp2_wif = 'KxtFy754kJc2KK5SWPR8UwfeXiRkXiQhNzk4pDoqBt17f5WSTt3D'

    def test_kp2(self):
#        return
        pk_from_wif = KeyPair.PrivateKeyFromWIF(self.kp2_wif)

#        print("pk from wif %s " % pk_from_wif)

        kp = KeyPair(priv_key=pk_from_wif)



    acd = b'\xb1\x81\x97]\x9f\x91W\x8c\x96\x00=\xe5\x1eH\xbar\x03\xdf\xcd\xa3;\xf9\x95\xe5u\xaf\xce\x92\xa7T\xe6A\xa7\xba\x93\xf6\xaf\xde\xc7\x8e\x90\xfd*d\xd5e\xad\xdb\xc1\xca[x\xe6<]\x08\x13\xcd\xd3Xt\x93\x95xeV\xd4B6\xd8Gp\x8a\xa5\xfc\xff\x93Q\xfa:\x95tk.\x98\xcb\xf5\xe0I\xa9}L\xde\xb0\xb9~'
    #ac_phash = '9f17653f6b2073f4f5813d45f0990bfc5307b205'
    ac_phash = '6c2d8b07cd1dc46f14d2fc1736cea4dbb3fc98cb'

    def test_decrypted_key(self):

        privkey = self.acd
        key = KeyPair(priv_key=privkey)
        self.assertEqual(self.ac_phash, key.PublicKeyHash.ToString())