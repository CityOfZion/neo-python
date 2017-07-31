
import unittest
#from neo.Core.Blockchain import Blockchain
from neo.Blockchain import GetBlockchain
from neo.Blockchain import GetGenesis
from neo.Blockchain import GetSystemCoin
from neo.Blockchain import GetSystemShare
import binascii
from neo.IO.Helper import AsSerializableWithType
import io
from neo.Core.Witness import Witness

class BlocksTestCase(unittest.TestCase):


    testnet_genesis_hash =      b'b3181718ef6167105b70920e4a8fbbd0a0a56aacf460d70e10ba6fa1668f1fef'
                               #b'a86943013e4a0eac66024723fa8689f355c85db674365fc9481a37d3ed5480ab' <-- current
    testnet_genesis_merkle =    b'c673a4b28f32ccb6d54cf721e8640d7a979def7cef5e4885bb085618ddeb38bd'
                               #b'7a9909d9a8fcf815bacb78b67de8b40936f24d78f7dcb90c0f1857db75a005fa' <-- current
    testnet_genesis_index = 0
    testnet_genesis_numtx = 4

    test_genesis_tx_hashes = [
        b'fb5bd72b2d6792d75dc2f1084ffa9e9f70ca85543c717a6b13d9959b452a57d6',
        b'c56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b',
        b'602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7',
        b'bdecbb623eee6f9ade28d5a8ff5fb3ea9c9d73af039e0286201b3b0291fb4d4a',
    ]

    rawblock = b'\x00\x00\x00\x00\xb7\xde\xf6\x81\xf0\x08\x02b\xaa)0q\xc5;A\xfc1F\xb1\x96\x06rCp\x0bh\xac\xd0YsO\xd1\x95C\x10\x8b\xf9\xdd\xc78\xcb\xee.\xd1\x16\x0f\x15:\xa0\xd0W\xf0b\xde\n\xa3\xcb\xb6K\xa8\x875\xc2=Cf~YT?\x05\x00\x95\xdf\x82\xb0.2L_\xf3\x81-\xb9\x82\xf3\xb0\x08\x9a!\xa2x\x98\x8e\xfe\xecj\x02{%\x01\xfdE\x01@\x11:\xc6fW\xc2\xf5D\xe8\xad\x13\x90_\xcb.\xba\xad\xfe\xf9P,\xbe\xfb\x07\x96\x0f\xbeV\xdf\t\x88\x14\xc2#\xdc\xdd=\x0e\xfa\x0bC\xa9E\x9eeM\x94\x85\x16\xdc\xbd\x8b7\x0fP\xfb\xec\xfb\x8bA\x1dH\x05\x1a@\x85\x00\xce\x85Y\x1eQe%\xdb$\x06T\x11\xf6\xa8\x8fC\xde\x90\xfa\x9c\x16|.oZ\xf4;\xc8Ne\xe5\xa4\xbb\x17K\xc8:\x19\xb6\x96_\xf1\x0fGk\x1b\x15\x1a\xe1T9\xa9\x85\xf39\x16\xab\xc6\x82+\x0b\xb1@\xf4\xaa\xe5"\xff\xae\xa2)\x98z\x10\xd0\x1b\xee\xc8&\xc3\xb9\xa1\x89\xfe\x02\xaa\x82h\x05\x81\xb7\x8f=\xf0\xeaM?\x93\xca\x8e\xa3_\xfc\x90\xf1_}\xb9\x01\x7f\x92\xfa\xfd\x93\x80\xd9\xba27\x97<\xf41<\xf6&\xfc@\xe3\x0eP\xe3X\x8b\xd0G\xb3\x9fG\x8bY28h\xcdP\xc7\xabT5]\x82E\xbf\x0f\x19\x88\xd3u(\xf9\xbb\xfch\x11\x0c\xf9\x17\xde\xbb\xdb\xf1\xf4\xbd\xd0,\xdc\xcc\xdc2i\xfd\xf1\x8alr~\xe5Ki4\xd8@\xe49\x18\xdd\x1e\xc6\x125P\xec7\xa5\x13\xe7+4\xb2\xc2\xa3\xba\xa5\x10\xde\xc3\x03|\xbe\xf2\xfa\x9fn\xd1\xe7\xcc\xd1\xf3\xf6\xe1\x9dL\xe2\xc0\x91\x9a\xf5RI\xa9p\xc2hR\x17\xf7ZU\x89\xcf\x9eT\xdf\xf8D\x9a\xf1U!\x02\t\xe7\xfdA\xdf\xb5\xc2\xf8\xdcr\xeb05\x8a\xc1\x00\xea\x8cr\xda\x18\x84{\xef\xe0n\xad\xe6\x8c\xeb\xfc\xb9!\x03\'\xda\x12\xb5\xc4\x02\x00\xe9\xf6UiGk\xbf\xf2!\x8d\xa4\xf3%H\xffC\xb68~\xc1Aj#\x1e\xe8!\x03O\xf5\xce\xea\xc4\x1a\xcf"\xcd^\xd2\xda\x17\xa6\xdfM\xd85\x8f\xcb+\xfb\x1aC \x8a\xd0\xfe\xaa\xb2tk!\x02l\xe3[)\x14z\xd0\x9eJ\xfeN\xc4\xa71\x90\x95\xf0\x81\x98\xfa\x8b\xab\xbe<V\xe9p\xb1CR\x8d"!\x03\x8d\xdd\xc0l\xe6\x87gzS\xd5O\tm%\x91\xba#\x02\x06\x8c\xf1#\xc1\xf2\xd7\\-\xdd\xc5BUy!\x03\x9d\xaf\xd8W\x1ad\x10X\xcc\xc82\xc5\xe2\x11\x1e\xa3\x9b\t\xc0\xbd\xe3`P\x91C\x84\xf7\xa4\x8b\xce\x9b\xf9!\x02\xd0+\x18s\xa0\x86<\xd0B\xccq}\xa3\x1c\xea\r|\xf9\xdb2\xb7MLr\xc0\x1b\x00\x11P>."W\xae\x01\x00\x00\x95\xdf\x82\xb0\x00\x00\x00\x00'
    rb_prev=b'd14f7359d0ac680b7043720696b14631fc413bc5713029aa620208f081f6deb7'
    rb_merlke=b'3dc23587a84bb6cba30ade62f057d0a03a150f16d12eeecb38c7ddf98b104395'
    rb_ts = 1501455939
    rb_h = 343892
    rconsenusdata = 6866918707944415125

    rblock_tx_id = b'3dc23587a84bb6cba30ade62f057d0a03a150f16d12eeecb38c7ddf98b104395'
                   #b'51296c00274738fe4c929063255d53bb815bc71c099dfa8930fb690eb73204af'
    rblock_tx_nonce=2961366933
    rblock_inputs = []
    rblock_outputs = []



    def test_block_deserialize(self):

        block = AsSerializableWithType(self.rawblock, 'neo.Core.Block.Block')

        self.assertEqual(self.rb_prev, block.PrevHash)
        self.assertEqual(self.rb_merlke, block.MerkleRoot)
        self.assertEqual(self.rb_ts, block.Timestamp)
        self.assertEqual(self.rb_h, block.Index)
        self.assertEqual(self.rconsenusdata, block.ConsensusData)

        tx = block.Transactions[0]

        self.assertEqual(tx.Nonce, self.rblock_tx_nonce)


        self.assertEqual(len(tx.inputs), 0)
        self.assertEqual(len(tx.outputs), 0)
        self.assertEqual(len(tx.Attributes), 0)


        self.assertEqual(type(tx.scripts), Witness)


    def test_genesis_block(self):
        return
        block = GetGenesis()
        print("block: %s " % block)
        print("merkle: %s " % block.MerkleRoot )
        hash = block.GetHashCode()
        merklehash = binascii.hexlify(block.MerkleRoot)
        tos = binascii.hexlify(hash)

        print("tost %s " % tos)
        print("merlke hash: %s " % merklehash)
        print("number of transactions: %s " % len(block.Transactions))


#        for tx in block.Transactions:
#            hash = binascii.hexlify(tx.Hash())
#            print("hash: %s " % hash)

        self.assertEqual(len(block.Transactions), self.testnet_genesis_numtx)
        self.assertEqual(block.Index, self.testnet_genesis_index)
        self.assertEqual(tos, self.testnet_genesis_hash)
        self.assertEqual(merklehash, self.testnet_genesis_merkle)