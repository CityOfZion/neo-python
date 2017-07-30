
import unittest
#from neo.Core.Blockchain import Blockchain
from neo.Blockchain import GetBlockchain
from neo.Blockchain import GetGenesis
from neo.Blockchain import GetSystemCoin
from neo.Blockchain import GetSystemShare
import binascii
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

    def test_genesis_block(self):

        block = GetGenesis()
        print("block: %s " % block)
        print("merkle: %s " % block.MerkleRoot )
        hash = block.GetHashCode()
        merklehash = binascii.hexlify(block.MerkleRoot)
        tos = binascii.hexlify(hash)

        print("tost %s " % tos)
        print("merlke hash: %s " % merklehash)
        print("number of transactions: %s " % len(block.Transactions))


        for tx in block.Transactions:
            hash = binascii.hexlify(tx.Hash())
            print("hash: %s " % hash)

        self.assertEqual(len(block.Transactions), self.testnet_genesis_numtx)
        self.assertEqual(block.Index, self.testnet_genesis_index)
        self.assertEqual(tos, self.testnet_genesis_hash)
        self.assertEqual(merklehash, self.testnet_genesis_merkle)