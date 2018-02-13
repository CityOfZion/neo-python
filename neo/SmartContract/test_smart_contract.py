from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.IO.Helper import Helper
from neo.Core.TX.Transaction import TransactionType

import binascii


class SmartContractTest(BlockchainFixtureTestCase):

    @classmethod
    def leveldb_testpath(self):
        return './fixtures/test_chain'

    def test_a_initial_setup(self):

        self.assertEqual(self._blockchain.Height, 758715)

    invb = b'00000000a94e2dacf44d6b4b1d2dd1929c6b77416201a2db8d0b762636b1098568159ab46d957d397ff13b229f4d122b70a0165ecadc6ef306bdc6b87e776613c42dd96912531359d3070000c6c7788f27c7322ef3812db982f3b0089a21a278988efeec6a027b2501fd450140eea7535f35ef9568f6e90bcac4c800e03f3c442670d2361bae5200ce26dca45f945735cb9363370ca31872ffc615d54dcf5833f72b1f82540d08162d0c1e936c4082b07301341f87e7a1b006698b39a1ca65829c26b02f405a4828359696b99c0ce91c6d3dcb4937f52d351373bb7208b42a92aad2df260c3c236a9e8f72465c1740b22665c229017775be08a2b874bb5e3acb4e8bedebbe328b18ee9f7c5e4842a17a801d6c4871e6c1740dbe77e72a1e29f49fd44a1a229802d6ad37512867714c40acd3f2543d1b15bd261f59f5d2011692981a3556e458e74d5855f4bb390ecc2f28c4874d21bdadecb9b25d5aec77d1acff4bce4a7e4633cf849230d7cb1b7cfa4085bdbc115dd0115d949b6b76bc74a2b6166f86d4f5b58ce38e11ea509291600973209d9f9718a336cd1c0e3ea9418643d39d3b216819cbd0f08393f643389575f155210209e7fd41dfb5c2f8dc72eb30358ac100ea8c72da18847befe06eade68cebfcb9210327da12b5c40200e9f65569476bbff2218da4f32548ff43b6387ec1416a231ee821034ff5ceeac41acf22cd5ed2da17a6df4dd8358fcb2bfb1a43208ad0feaab2746b21026ce35b29147ad09e4afe4ec4a7319095f08198fa8babbe3c56e970b143528d2221038dddc06ce687677a53d54f096d2591ba2302068cf123c1f2d75c2dddc542557921039dafd8571a641058ccc832c5e2111ea39b09c0bde36050914384f7a48bce9bf92102d02b1873a0863cd042cc717da31cea0d7cf9db32b74d4c72c01b0011503e2e2257ae020000c6c7788f00000000d100644011111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111081234567890abcdef0415cd5b0769cc4ee2f1c9f4e0782756dabf246d0a4fe60a035400000000'
    invbh = b'0f72795fd62d5e7eeb65ce1452388343224cbc43cf56a0e8af866db07209a43c'
    invtxh = '4011111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111081234567890abcdef0415cd5b0769cc4ee2f1c9f4e0782756dabf246d0a4fe60a0354'

    def test_a_invocation_block(self):

        hexdata = binascii.unhexlify(self.invb)

        block = Helper.AsSerializableWithType(hexdata, 'neo.Core.Block.Block')

        self.assertEqual(block.Hash.ToBytes(), self.invbh)
        self.assertEqual(block.Index, 2003)

        invtx = None
        for tx in block.Transactions:
            if tx.Type == TransactionType.InvocationTransaction:
                invtx = tx

        self.assertIsNotNone(invtx)

        self.assertEqual(len(invtx.Script), 100)
        self.assertEqual(invtx.Script.hex(), self.invtxh)

    def test_a_run_sc(self):

        hexdata = binascii.unhexlify(self.invb)

        block = Helper.AsSerializableWithType(hexdata, 'neo.Core.Block.Block')

        result = self._blockchain.Persist(block)

        self.assertTrue(result)
