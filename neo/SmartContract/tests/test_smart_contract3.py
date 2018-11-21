import binascii
import os
from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.IO.Helper import Helper
from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.DBCollection import DBCollection
from neo.Implementations.Blockchains.LevelDB.DBPrefix import DBPrefix
from neo.Core.State.ContractState import ContractState
from neo.Core.State.AssetState import AssetState
from neocore.UInt256 import UInt256
from neocore.Cryptography.Crypto import Crypto
from neo.Settings import settings


class SmartContractTest3(BlockchainFixtureTestCase):

    @classmethod
    def leveldb_testpath(cls):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    contract_create_block = b'000000007134e5ee56f841bb73dbff969a9ef793c05f175cd386b2f24874a54c441cc0500e6c4e19da72fd4956a28670f36d26e03fd43c1794a1d3a5ad4f738dd48b53f505c7605b992400006b76abd322b7bd0bbe48d3a3f5d10013ab9ffee489706078714f1ea201c3400df8020bf9c22cd865b43b73060be3302abbab95b5f38941ba288cd77b846c9c1edcef1ab9a108f0a2fb8180e88178d3e85e316243054e48b29ced9dde54766340d9efc4f6d78970aba6712688071b862413bd53d58620e87c951aa3eac5c2611cdfecfcf084c12cfbe6cd356ef7726b9b5e93c10b5ffa7dc6e77ae8dc8c7af09240756caac1dad30a93662f36194fe270bb2afe0a557492122027df5f95dc5b1b9d18b169a6a96795019067ba008e5d42250c23886f0807ec20f3c880b2e740d1048b532102103a7f7dd016558597f7960d27c516a4394fd968b9e65155eb4b013e4040406e2102a7bc55fe8684e0119768d104ba30795bdcc86619e864add26156723ed185cd622102b3622bf4017bdfe317c58aed5f4c753f206b7db896046fa7d774bbc4bf7f8dc22103d90c07df63e690ce77912e10ab51acc944b66860237b608c4f8f8309e71ee69954ae0200006b76abd300000000d101de39202f726f6f742f2e6e656f707974686f6e2f436861696e732f556e6974546573742d534d2f636f6e7472616374732f73616d706c65322e70790474657374047465737404746573740474657374000102030702024c725ec56b6a00527ac46a51527ac46a52527ac46a00c3036164649c640d006a51c36a52c3936c7566616a00c3037375629c640d006a51c36a52c3946c7566616a00c3036d756c9c640d006a51c36a52c3956c7566616a00c3036469769c640d006a51c36a52c3966c7566614f6c7566006c756668134e656f2e436f6e74726163742e437265617465001a7118020000000001347fff9221a8caf429279a82906688eb78264c1a9a2791d95ee47b6e095120aa000001e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c600080b5fc5c02000023ba2703c53263e8d6e522dc32203339dcd8eee90141405787dc8c47ba7da02668582b822bb50e1b615546a5f01826967cba603a0744a01aed6c098d809f20ec199a84269aa01ea911564effe7c1b4ad65d71f4ca995a12321031a6c6fbbdf02ca351745fa86b9ba5a9452d785ac4f7fc2b7548ca2a46c4fcf4aac'
    contract_hash = b'86d58778c8d29e03182f38369f0d97782d303cc0'
    contract_block_index = 9369
    contract_block_script = b'5ec56b6a00527ac46a51527ac46a52527ac46a00c3036164649c640d006a51c36a52c3936c7566616a00c3037375629c640d006a51c36a52c3946c7566616a00c3036d756c9c640d006a51c36a52c3956c7566616a00c3036469769c640d006a51c36a52c3966c7566614f6c7566006c7566'

    def test_contract_create_block(self):

        hexdata = binascii.unhexlify(self.contract_create_block)

        block = Helper.AsSerializableWithType(hexdata, 'neo.Core.Block.Block')

        self.assertEqual(block.Index, self.contract_block_index)

        result = Blockchain.Default().Persist(block)

        self.assertTrue(result)

        contracts = DBCollection(Blockchain.Default()._db, DBPrefix.ST_Contract, ContractState)

        contract_added = contracts.TryGet(self.contract_hash)

        self.assertIsNotNone(contract_added)

        self.assertEqual(contract_added.HasStorage, False)
        self.assertEqual(contract_added.Name, b'test')
        self.assertEqual(contract_added.Email, b'test')

        self.assertEqual(len(Blockchain.Default().SearchContracts("test NEX Template V3")), 1)
        self.assertEqual(len(Blockchain.Default().SearchContracts("TEST nex TEMPLATE v3")), 1)
        self.assertEqual(len(Blockchain.Default().SearchContracts("TEST!")), 0)

        code = contract_added.Code

        self.assertIsNotNone(code)

        self.assertEqual(code.ReturnType, 2)

        self.assertEqual(code.ScriptHash().ToBytes(), self.contract_hash)
        self.assertEqual(code.Script.hex().encode('utf-8'), self.contract_block_script)

    asset_create_block = b'000000007134e5ee56f841bb73dbff969a9ef793c05f175cd386b2f24874a54c441cc0500e6c4e19da72fd4956a28670f36d26e03fd43c1794a1d3a5ad4f738dd48b53f505c7605b992400006b76abd322b7bd0bbe48d3a3f5d10013ab9ffee489706078714f1ea201c3400df8020bf9c22cd865b43b73060be3302abbab95b5f38941ba288cd77b846c9c1edcef1ab9a108f0a2fb8180e88178d3e85e316243054e48b29ced9dde54766340d9efc4f6d78970aba6712688071b862413bd53d58620e87c951aa3eac5c2611cdfecfcf084c12cfbe6cd356ef7726b9b5e93c10b5ffa7dc6e77ae8dc8c7af09240756caac1dad30a93662f36194fe270bb2afe0a557492122027df5f95dc5b1b9d18b169a6a96795019067ba008e5d42250c23886f0807ec20f3c880b2e740d1048b532102103a7f7dd016558597f7960d27c516a4394fd968b9e65155eb4b013e4040406e2102a7bc55fe8684e0119768d104ba30795bdcc86619e864add26156723ed185cd622102b3622bf4017bdfe317c58aed5f4c753f206b7db896046fa7d774bbc4bf7f8dc22103d90c07df63e690ce77912e10ab51acc944b66860237b608c4f8f8309e71ee69954ae0200006b76abd300000000d101de39202f726f6f742f2e6e656f707974686f6e2f436861696e732f556e6974546573742d534d2f636f6e7472616374732f73616d706c65322e70790474657374047465737404746573740474657374000102030702024c725ec56b6a00527ac46a51527ac46a52527ac46a00c3036164649c640d006a51c36a52c3936c7566616a00c3037375629c640d006a51c36a52c3946c7566616a00c3036d756c9c640d006a51c36a52c3956c7566616a00c3036469769c640d006a51c36a52c3966c7566614f6c7566006c756668134e656f2e436f6e74726163742e437265617465001a7118020000000001347fff9221a8caf429279a82906688eb78264c1a9a2791d95ee47b6e095120aa000001e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c600080b5fc5c02000023ba2703c53263e8d6e522dc32203339dcd8eee90141405787dc8c47ba7da02668582b822bb50e1b615546a5f01826967cba603a0744a01aed6c098d809f20ec199a84269aa01ea911564effe7c1b4ad65d71f4ca995a12321031a6c6fbbdf02ca351745fa86b9ba5a9452d785ac4f7fc2b7548ca2a46c4fcf4aac'
    asset_create_index = 9369

    asset_create_id = b'602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7'
    asset_admin = 'AWKECj9RD8rS8RPcpCgYVjk1DeYyHwxZm3'

    def test_invocation_assetcreate_block(self):

        hexdata = binascii.unhexlify(self.asset_create_block)

        block = Helper.AsSerializableWithType(hexdata, 'neo.Core.Block.Block')

        self.assertEqual(block.Index, self.asset_create_index)

        result = Blockchain.Default().Persist(block)

        self.assertTrue(result)

        # now the asset that was created should be there
        assets = DBCollection(Blockchain.Default()._db, DBPrefix.ST_Asset, AssetState)

        newasset = assets.TryGet(self.asset_create_id)

        self.assertIsNotNone(newasset)

        self.assertEqual(newasset.AssetType, 1)
        self.assertEqual(newasset.Precision, 8)
        self.assertEqual(Crypto.ToAddress(newasset.Admin), self.asset_admin)
        self.assertEqual(Crypto.ToAddress(newasset.Issuer), self.asset_admin)
        self.assertIsInstance(newasset.AssetId, UInt256)
        self.assertEqual(newasset.AssetId.ToBytes(), self.asset_create_id)
