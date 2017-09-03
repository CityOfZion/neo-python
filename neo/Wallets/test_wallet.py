from neo.Utils.NeoTestCase import NeoTestCase
from neo.Wallets.KeyPair import KeyPair
from neo.UInt160 import UInt160
from neo.SmartContract.Contract import Contract
import binascii
from neo.Core.Helper import Helper
from neo.IO.MemoryStream import StreamManager
from neo.IO.BinaryReader import BinaryReader
from neo.Cryptography.Crypto import Crypto
from neo.Core.TX.Transaction import Transaction
from neo.VM.ScriptBuilder import ScriptBuilder
from neo.VM import OpCode

import json

class WalletTestCase(NeoTestCase):


    iv= b'x\xdb\xa9\xc8\xd8\xb6\x80A\xf3Y\xb4:\x8b\xf03\xf1'
    mk= b'k\xcc\xf3\xb6\x94\x16\xc8\x86\xc2\xd5\xc6\xdam\xd8^D\x87c\x17\xd7G\xb8w\x86 \xffD\xac\x80X\xf0\xa3'
    pk= b'p\x8a/d\xd7\xcc\xeedr\x91\xd1^3{\x9d"8/\x82H\xb6\x9bu\xeb\xe6\x84\xe6f\xb0m\x12&'

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
        return
        key = KeyPair(priv_key=self.pk)

        self.assertEqual(key.PublicKey.x, self.pubkey_x)
        self.assertEqual(key.PublicKey.y, self.pubkey_y)

        print("PUBKEY X/Y %s %s " % (key.PublicKey.x.value, type(key.PublicKey.x.value)))

        self.assertEqual(key.PublicKey.encode_point(True), self.pubkey_encoded)
        self.assertEqual(key.PublicKey.encode_point(False), self.pubkey_not_comp)

        self.assertIsInstance(key.PublicKeyHash, UInt160)

        self.assertEqual(key.PublicKeyHash.ToBytes(), self.pubkeyhash)
        self.assertEqual(key.Export(), self.wif)


        private_key_from_wif = KeyPair.PrivateKeyFromWIF(self.wif)

        self.assertEqual(private_key_from_wif, self.pk)


    def test_b(self):
        return
        key = KeyPair(priv_key=self.pk)

        contract = Contract.CreateSignatureContract(key.PublicKey)

        self.assertEqual(binascii.unhexlify(contract.Script), self.contract_script)
        self.assertEqual(contract.ScriptHash.ToBytes(), self.contract_script_hash)

        self.assertEqual(contract.Address, self.contract_address)

        self.assertEqual(contract.PublicKeyHash, key.PublicKeyHash)
        self.assertEqual(contract.PublicKeyHash.ToBytes(), self.pubkeyhash)


    def test_c(self):
        return
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




    sig_prik = b'~/\xb6\xf3RG\xb7\xf9\xd3;\xf8\x1d<k\t\xc0u<}@\x9f\xe5\xf6\xcb\xabG\x0e,\x90*s\xd8'
    sig_pubk =b"\x04\x86\xc2't\x97\xe8--\x0f\\\x11*\xa1uT_\xd6\x8a\xc0K\x06\xec\rA#\xd4\xb5\xeej\x1cZl\x97\xcbB\x0e@\xb4\x90\x12\xd5\xbdl\x1e\xb7\xe1D\xf5w\x80\xef\xe0\x8di\x89\xa8\xa2?\x86Z2z\x99\xec"


    sig_message = b'\x80\x00\x00\x01\xec\x7f\xd0L_x/\xeaQ\x86\x01"\xbb\xe1\x06\x82\xc3l\xc4\x8c\xb4v\xbf\x11\xb6 \xc7\xc2\x06\xc5\x85\xc0\x01\x00\x02\x9b|\xff\xda\xa6t\xbe\xae\x0f\x93\x0e\xbe`\x85\xaf\x90\x93\xe5\xfeV\xb3J\\"\x0c\xcd\xcfn\xfc3o\xc5\x00\xeaV\xfa\x00\x00\x00\x00<w.\xba\x0f\xbeT\x82#>?+qnA\x10\xa4-\x1a\xac\x9b|\xff\xda\xa6t\xbe\xae\x0f\x93\x0e\xbe`\x85\xaf\x90\x93\xe5\xfeV\xb3J\\"\x0c\xcd\xcfn\xfc3o\xc5\x00\xa6\x8b\x95y\x00\x00\x00\x01\x0c\xedx\xd6\xaa\xccE\xc7X\xb7#A\x1b_\xd7\x13\x98\x8c4'

    sig_result = b"\xa0=\x8f\xa2\xb0w\xe6\xa4q?c\xe9<\xb0\xa8\xaf\x9a,\x8a\xc1\xa3c\xdeP\xf5\xd1\x8f\xa7\x01=n\x8f\x0e\x92c\xc8\xace'wZ\xd5O\xc3\xc2:i\xb0\x9cc\x83\xa5\x98[\xcb\xcc1*\x88\x1e]\xc9t\x89"
    sigresult_hex = b'a03d8fa2b077e6a4713f63e93cb0a8af9a2c8ac1a363de50f5d18fa7013d6e8f0e9263c8ac6527775ad54fc3c23a69b09c6383a5985bcbcc312a881e5dc97489'

    pload = b'\x80\x00\x00\x01\xd0\xcbW\x05q}]\x9e\x91\xd0\x07\xa11\x05\xff\xf3b\x95\xc0\xcb\xd48\x86\x9b\x82\xe7\xde\x00\x15\x96\n\xe2\x00\x00\x02\x9b|\xff\xda\xa6t\xbe\xae\x0f\x93\x0e\xbe`\x85\xaf\x90\x93\xe5\xfeV\xb3J\\"\x0c\xcd\xcfn\xfc3o\xc5\x00NrS\x00\x00\x00\x00\x01\x0c\xedx\xd6\xaa\xccE\xc7X\xb7#A\x1b_\xd7\x13\x98\x8c4\x9b|\xff\xda\xa6t\xbe\xae\x0f\x93\x0e\xbe`\x85\xaf\x90\x93\xe5\xfeV\xb3J\\"\x0c\xcd\xcfn\xfc3o\xc5\x00\x9c\xe4\xa6\x00\x00\x00\x00<w.\xba\x0f\xbeT\x82#>?+qnA\x10\xa4-\x1a\xac\x01A@\x19\xb3\x80zf\xbeA\xf4l\xc20\x8dY\xa6C<r>\xf2i\xe2\xe5\xc1\x07\x16\\\\\xfb\xe9\x96\xa2\x9a\xae\x99\xe9L\x93\x8f\x10\xb3\x85\xb4\x05\x19\xb4g+cVP\x0f\xf5\x98\xd6\xf2-\x94\x80\xb5\xec\xfex\x9f{#!\x03\x7f\xe2\x939\xae\x98\x9a\xadN8\xe3\x8f\xadk\x95\xed<c%/\xbb\xf4o\xcb\xe9\xe2\x1fI[dYT\xac'
    ploadh = '80000001d0cb5705717d5d9e91d007a13105fff36295c0cbd438869b82e7de0015960ae20000029b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500a3e11100000000010ced78d6aacc45c758b723411b5fd713988c349b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc5004775e8000000003c772eba0fbe5482233e3f2b716e4110a42d1aac014140d0a9a498a27e7e79531a81293357c75c0e3f1e2665491729d2bda6766e2108890789679bcae6021169b72dc83fff7696008018715d237afca8ac58035e54a4742321037fe29339ae989aad4e38e38fad6b95ed3c63252fbbf46fcbe9e21f495b645954ac'
    ploadh2= '80000001D0CB5705717D5D9E91D007A13105FFF36295C0CBD438869B82E7DE0015960AE20000029B7CFFDAA674BEAE0F930EBE6085AF9093E5FE56B34A5C220CCDCF6EFC336FC500A3E11100000000010CED78D6AACC45C758B723411B5FD713988C349B7CFFDAA674BEAE0F930EBE6085AF9093E5FE56B34A5C220CCDCF6EFC336FC5004775E8000000003C772EBA0FBE5482233E3F2B716E4110A42D1AAC'

    def test_sig(self):
        return
        key = KeyPair(priv_key=self.sig_prik)

        keypub = binascii.unhexlify(key.PublicKey.encode_point(False))
 #       print("key pub %s " % keypub)

        self.assertEqual(keypub, self.sig_pubk)

        stream = StreamManager.GetStream(data=binascii.unhexlify(self.ploadh))
        reader = BinaryReader(stream)
        tx = Transaction.DeserializeFrom(reader)
#        print("TX %s " % (json.dumps(tx.ToJson(), indent=4)))

        sig = Crypto.Sign(self.sig_message,key.PrivateKey, key.PublicKey)

        sb = ScriptBuilder()

        sb.push(binascii.hexlify(sig))




#        print("SB TO ARRAY %s  " % sb.ToArray())
#        print("SIG: %s %s" % (sig,len(sig)))
#        print("Sig hex %s " % sig.hex())


#        print("sig %s " % sig)

        res = Crypto.VerifySignature(self.sig_message, sig, key.PublicKey)

        self.assertTrue(res)


    mpk = b'\xd5\x8e\xc1J\xd7>\x01Y\x7f\xda5\x14gH<+\xddv\x19\xc0\xe3\xa2\xd0OT\xae\xf0b`\xb6\x17g'
    mppk= b'033838f3215bf05882c2ae37505a7f984197f7edce247f82aacad5f324354336ff'
    smes = b'80000001c6d9ba0c972fe595a9bebb48f1616daa1a09d852cc9861b18e1efec6021a89a70000029b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc50065cd1d00000000010ced78d6aacc45c758b723411b5fd713988c349b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc50020bcbe0000000049bc7ccb4e65a90d6067d8b171d66db0eab70d9d'
    smesm = b'80000001c6d9ba0c972fe595a9bebb48f1616daa1a09d852cc9861b18e1efec6021a89a70000029b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc50065cd1d00000000010ced78d6aacc45c758b723411b5fd713988c349b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc50020bcbe0000000049bc7ccb4e65a90d6067d8b171d66db0eab70d9d014140849e1609f2c6644e13cc3eb8a0c9bf2559bc6a0123f0ad7dfda4ae6a4355155ce0bfbb19a167932f63666ab469880e38197eb7eacf1e5a2e85b51c2b623ff98c2321033838f3215bf05882c2ae37505a7f984197f7edce247f82aacad5f324354336ffac'

    def test_sig2(self):

        key = KeyPair(priv_key=self.mpk)
        self.assertEqual(key.PublicKey.encode_point(True),self.mppk)

        sig = Crypto.Sign(self.sig_message,key.PrivateKey, key.PublicKey)

        print("sig: %s " % sig)
#        print("key pubkey %s " % key.PublicKey.encode_point(True))

#        res = Crypto.VerifySignature(self.sig_message, sig, key.PublicKey)

#        self.assertTrue(res)