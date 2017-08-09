import unittest
from neo.Core.TX.RegisterTransaction import RegisterTransaction
from neo.Core.TX.MinerTransaction import MinerTransaction
from neo.Core.TX.IssueTransaction import IssueTransaction
from neo.Core.TX.Transaction import *
from neo.Wallets.Contract import Contract
from neo.Core.Blockchain import Blockchain
from neo.Core.Helper import Helper
from neo.Core.Witness import Witness
from neo.Core.Scripts.ScriptOp import ScriptOp
from neo import Settings

class GenesisBlockTestCase(unittest.TestCase):

    testnet_genesis_hash = 'b3181718ef6167105b70920e4a8fbbd0a0a56aacf460d70e10ba6fa1668f1fef'
    testnet_ghash_current= ''
    # b'a86943013e4a0eac66024723fa8689f355c85db674365fc9481a37d3ed5480ab' <-- current
    testnet_genesis_merkle = b'c673a4b28f32ccb6d54cf721e8640d7a979def7cef5e4885bb085618ddeb38bd'

    testnet_genesis_raw = b'000000000000000000000000000000000000000000000000000000000000000000000000bd38ebdd185608bb85485eef7cef9d977a0d64e821f74cd5b6cc328fb2a473c665fc8857000000001dac2b7c00000000f3812db982f3b0089a21a278988efeec6a027b25'
    currraw             = b'000000000000000000000000000000000000000000000000000000000000000000000000bd38ebdd185608bb85485eef7cef9d977a0d64e821f74cd5b6cc328fb2a473c665fc8857000000001dac2b7c00000000f3812db982f3b0089a21a278988efeec6a027b25'

    # b'7a9909d9a8fcf815bacb78b67de8b40936f24d78f7dcb90c0f1857db75a005fa' <-- current
    testnet_genesis_index = 0
    testnet_genesis_numtx = 4
    testnet_genesis_nonce = 2083236893
    genblock_timestamp = 1468595301

    sys_share_id =  b'c56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b'
    sys_coin_id =   b'602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7'

    sysshareraw=    b'400000455b7b226c616e67223a227a682d434e222c226e616d65223a22e5b08fe89a81e882a1227d2c7b226c616e67223a22656e222c226e616d65223a22416e745368617265227d5d0000c16ff28623000000da1745e9b549bd0bfa1a569971c77eba30cd5a4b000000'
    syscoinraw =    b'400001445b7b226c616e67223a227a682d434e222c226e616d65223a22e5b08fe89a81e5b881227d2c7b226c616e67223a22656e222c226e616d65223a22416e74436f696e227d5d0000c16ff286230008009f7fd096d37ed2c0e3f7f0cfc924beef4ffceb68000000'

    gen_miner_tx_id = b'fb5bd72b2d6792d75dc2f1084ffa9e9f70ca85543c717a6b13d9959b452a57d6'
    gen_issue_tx_id = b'bdecbb623eee6f9ade28d5a8ff5fb3ea9c9d73af039e0286201b3b0291fb4d4a'

    contractraw=    b'54210209e7fd41dfb5c2f8dc72eb30358ac100ea8c72da18847befe06eade68cebfcb9210327da12b5c40200e9f65569476bbff2218da4f32548ff43b6387ec1416a231ee821034ff5ceeac41acf22cd5ed2da17a6df4dd8358fcb2bfb1a43208ad0feaab2746b21026ce35b29147ad09e4afe4ec4a7319095f08198fa8babbe3c56e970b143528d2221038dddc06ce687677a53d54f096d2591ba2302068cf123c1f2d75c2dddc542557921039dafd8571a641058ccc832c5e2111ea39b09c0bde36050914384f7a48bce9bf92102d02b1873a0863cd042cc717da31cea0d7cf9db32b74d4c72c01b0011503e2e2257ae'


    issuetx_rraw = b'01000000019b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc50000c16ff2862300197ff6783d512a740d42f4cc4f5572955fa44c95'

    test_genesis_tx_hashes = [
        b'fb5bd72b2d6792d75dc2f1084ffa9e9f70ca85543c717a6b13d9959b452a57d6',
        b'c56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b',
        b'602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7',
        b'bdecbb623eee6f9ade28d5a8ff5fb3ea9c9d73af039e0286201b3b0291fb4d4a',
    ]

    @classmethod
    def setUpClass(cls):
        if Settings.MAGIC == 1953787457:
            print('ok to test!')
        else:
            raise unittest.SkipTest('Only test genesis blocks with testnet protocol settings')

    def test_miner_tx(self):
        miner_tx = MinerTransaction()
        miner_tx.Nonce = 2083236893
        self.assertEqual(miner_tx.HashToByteString(), self.gen_miner_tx_id)

    def test_issue_tx(self):

        miner_tx = MinerTransaction()
        miner_tx.Nonce = 2083236893

        share_tx = GetSystemShare()
        coin_tx = GetSystemCoin()

        script = Contract.CreateMultiSigRedeemScript(int(len(Blockchain.StandbyValidators()) / 2) + 1, Blockchain.StandbyValidators())

        self.assertEqual(script, self.contractraw)
        out = Helper.RawBytesToScriptHash(script)

        output = TransactionOutput(
            share_tx.HashToByteString(),
            Blockchain.SystemShare().Amount,
            out
        )

        script = Witness( bytearray(0), bytearray(ScriptOp.PUSHT))

        issue_tx = IssueTransaction([],[output],[], [script])

        self.assertEqual(issue_tx.GetHashData(), self.issuetx_rraw)
        self.assertEqual(issue_tx.HashToByteString(), self.gen_issue_tx_id)

    def test_system_share(self):

        share_tx = GetSystemShare()

        self.assertEqual(type(share_tx), RegisterTransaction)
        self.assertEqual(self.sysshareraw, share_tx.GetHashData())
        self.assertEqual(self.sys_share_id, share_tx.HashToByteString())
        self.assertEqual(share_tx.Precision, 0)


    def test_system_coin(self):
        coin_tx = GetSystemCoin()
        self.assertEqual(type(coin_tx), RegisterTransaction)
        self.assertEqual(self.syscoinraw, coin_tx.GetHashData())
        self.assertEqual(self.sys_coin_id, coin_tx.HashToByteString())
        self.assertEqual(coin_tx.Precision, 8)

    def test_genesis_block(self):

        block = GetGenesis()

        self.assertEqual(len(block.Transactions), self.testnet_genesis_numtx)
        self.assertEqual(block.Index, self.testnet_genesis_index)
        self.assertEqual(block.ConsensusData, self.testnet_genesis_nonce)
        self.assertEqual(block.Timestamp, self.genblock_timestamp)
        self.assertEqual(block.MerkleRoot, self.testnet_genesis_merkle)

        txhashes = [tx.HashToByteString() for tx in block.Transactions]
        self.assertEqual(txhashes, self.test_genesis_tx_hashes)


        rd = block.RawData()

        self.assertEqual(block.RawData(), self.testnet_genesis_raw)
        self.assertEqual(block.HashToString(), self.testnet_genesis_hash)
