from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.IO.Helper import Helper
from neo.Core.TX.Transaction import TransactionType
from neo.Settings import settings
import os
import binascii


class SmartContractTest(BlockchainFixtureTestCase):

    @classmethod
    def leveldb_testpath(cls):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    # test need to be updated whenever we change the fixtures
    def test_a_initial_setup(self):
        self.assertEqual(self._blockchain.Height, 12349)

    invb = b'000000007134e5ee56f841bb73dbff969a9ef793c05f175cd386b2f24874a54c441cc0500e6c4e19da72fd4956a28670f36d26e03fd43c1794a1d3a5ad4f738dd48b53f505c7605b992400006b76abd322b7bd0bbe48d3a3f5d10013ab9ffee489706078714f1ea201c3400df8020bf9c22cd865b43b73060be3302abbab95b5f38941ba288cd77b846c9c1edcef1ab9a108f0a2fb8180e88178d3e85e316243054e48b29ced9dde54766340d9efc4f6d78970aba6712688071b862413bd53d58620e87c951aa3eac5c2611cdfecfcf084c12cfbe6cd356ef7726b9b5e93c10b5ffa7dc6e77ae8dc8c7af09240756caac1dad30a93662f36194fe270bb2afe0a557492122027df5f95dc5b1b9d18b169a6a96795019067ba008e5d42250c23886f0807ec20f3c880b2e740d1048b532102103a7f7dd016558597f7960d27c516a4394fd968b9e65155eb4b013e4040406e2102a7bc55fe8684e0119768d104ba30795bdcc86619e864add26156723ed185cd622102b3622bf4017bdfe317c58aed5f4c753f206b7db896046fa7d774bbc4bf7f8dc22103d90c07df63e690ce77912e10ab51acc944b66860237b608c4f8f8309e71ee69954ae0200006b76abd300000000d101de39202f726f6f742f2e6e656f707974686f6e2f436861696e732f556e6974546573742d534d2f636f6e7472616374732f73616d706c65322e70790474657374047465737404746573740474657374000102030702024c725ec56b6a00527ac46a51527ac46a52527ac46a00c3036164649c640d006a51c36a52c3936c7566616a00c3037375629c640d006a51c36a52c3946c7566616a00c3036d756c9c640d006a51c36a52c3956c7566616a00c3036469769c640d006a51c36a52c3966c7566614f6c7566006c756668134e656f2e436f6e74726163742e437265617465001a7118020000000001347fff9221a8caf429279a82906688eb78264c1a9a2791d95ee47b6e095120aa000001e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c600080b5fc5c02000023ba2703c53263e8d6e522dc32203339dcd8eee90141405787dc8c47ba7da02668582b822bb50e1b615546a5f01826967cba603a0744a01aed6c098d809f20ec199a84269aa01ea911564effe7c1b4ad65d71f4ca995a12321031a6c6fbbdf02ca351745fa86b9ba5a9452d785ac4f7fc2b7548ca2a46c4fcf4aac'
    invbh = b'ac2d9d876bb6ee5cf1d011820409180cda7594b88c94f94a110ce2f5e472294e'
    invtxh = '39202f726f6f742f2e6e656f707974686f6e2f436861696e732f556e6974546573742d534d2f636f6e7472616374732f73616d706c65322e70790474657374047465737404746573740474657374000102030702024c725ec56b6a00527ac46a51527ac46a52527ac46a00c3036164649c640d006a51c36a52c3936c7566616a00c3037375629c640d006a51c36a52c3946c7566616a00c3036d756c9c640d006a51c36a52c3956c7566616a00c3036469769c640d006a51c36a52c3966c7566614f6c7566006c756668134e656f2e436f6e74726163742e437265617465'

    def test_a_invocation_block(self):

        hexdata = binascii.unhexlify(self.invb)

        block = Helper.AsSerializableWithType(hexdata, 'neo.Core.Block.Block')

        self.assertEqual(block.Hash.ToBytes(), self.invbh)
        self.assertEqual(block.Index, 9369)

        invtx = None
        for tx in block.Transactions:
            if tx.Type == TransactionType.InvocationTransaction:
                invtx = tx

        self.assertIsNotNone(invtx)

        self.assertEqual(len(invtx.Script), 222)
        self.assertEqual(invtx.Script.hex(), self.invtxh)

    def test_a_run_sc(self):

        hexdata = binascii.unhexlify(self.invb)

        block = Helper.AsSerializableWithType(hexdata, 'neo.Core.Block.Block')

        result = self._blockchain.Persist(block)

        self.assertTrue(result)
