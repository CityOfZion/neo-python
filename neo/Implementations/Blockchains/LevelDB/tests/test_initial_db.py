from neo.Utils.NeoTestCase import NeoTestCase
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Core.Blockchain import Blockchain
from neo.IO.Helper import Helper
from neo.Settings import settings
import shutil
import binascii
import os


class LevelDBTest(NeoTestCase):

    LEVELDB_TESTPATH = os.path.join(settings.DATA_DIR_PATH, 'UnitTestChain')

    _blockchain = None

    _genesis = None

    block_one_raw = b'00000000ef1f8f66a16fba100ed760f4ac6aa5a0d0bb8f4a0e92705b106761ef181718b3d0765298ceb5f57de7d2b0dab00ed25be4134706ada2d90adb8b7e3aba323a8e1abd125901000000d11f7a289214bdaff3812db982f3b0089a21a278988efeec6a027b2501fd450140884037dd265cb5f5a54802f53c2c8593b31d5b8a9c0bad4c7e366b153d878989d168080ac36b930036a9eb966b48c70bb41792e698fa021116f27c09643563b840e83ab14404d964a91dbac45f5460e88ad57196b1779478e3475334af8c1b49cd9f0213257895c60b5b92a4800eb32d785cbb39ae1f022528943909fd37deba63403677848bf98cc9dbd8fbfd7f2e4f34471866ea82ca6bffbf0f778b6931483700c17829b4bd066eb04983d3aac0bd46b9c8d03a73a8e714d3119de93cd9522e314054d16853b22014190063f77d9edf6fbccefcf71fffd1234f688823b4e429ae5fa639d0a664c842fbdfcb4d6e21f39d81c23563b92cffa09696d93c95bc4893a6401a43071d00d3e854f7f1f321afa7d5301d36f2195dc1e2643463f34ae637d2b02ae0eb11d4256c507a4f8304cea6396a7fce640f50acb301c2f6336d27717e84f155210209e7fd41dfb5c2f8dc72eb30358ac100ea8c72da18847befe06eade68cebfcb9210327da12b5c40200e9f65569476bbff2218da4f32548ff43b6387ec1416a231ee821034ff5ceeac41acf22cd5ed2da17a6df4dd8358fcb2bfb1a43208ad0feaab2746b21026ce35b29147ad09e4afe4ec4a7319095f08198fa8babbe3c56e970b143528d2221038dddc06ce687677a53d54f096d2591ba2302068cf123c1f2d75c2dddc542557921039dafd8571a641058ccc832c5e2111ea39b09c0bde36050914384f7a48bce9bf92102d02b1873a0863cd042cc717da31cea0d7cf9db32b74d4c72c01b0011503e2e2257ae010000d11f7a2800000000'
    block_one_hash = b'0012f8566567a9d7ddf25acb5cf98286c9703297de675d01ba73fbfe6bcb841c'

    @classmethod
    def setUpClass(cls):
        settings.setup_unittest_net()
        Blockchain.DeregisterBlockchain()
        cls._blockchain = LevelDBBlockchain(path=cls.LEVELDB_TESTPATH, skip_version_check=True)
        Blockchain.RegisterBlockchain(cls._blockchain)
        cls._genesis = Blockchain.GenesisBlock()

    @classmethod
    def tearDownClass(cls):
        cls._blockchain.Dispose()
        shutil.rmtree(cls.LEVELDB_TESTPATH)

    def test__initial_state(self):

        self.assertEqual(self._blockchain.CurrentBlockHash, self._genesis.Hash.ToBytes())

        self.assertEqual(self._blockchain.CurrentHeaderHash, self._genesis.Header.Hash.ToBytes())

        self.assertEqual(self._blockchain.CurrentHeaderHash, self._genesis.Header.Hash.ToBytes())

        self.assertEqual(self._blockchain.HeaderHeight, 0)

        self.assertEqual(self._blockchain.Height, 0)

    def test_add_header(self):
        hexdata = binascii.unhexlify(self.block_one_raw)
        block_one = Helper.AsSerializableWithType(hexdata, 'neo.Core.Block.Block')

        if settings.MAGIC == 56753:
            self.assertEqual(self._blockchain.CurrentHeaderHash, b'996e37358dc369912041f966f8c5d8d3a8255ba5dcbd3447f8a82b55db869099')
        else:
            self.assertEqual(self._blockchain.CurrentHeaderHash, b'd42561e3d30e15be6400b6df2f328e02d2bf6354c41dce433bc57687c82144bf')

        self.assertEqual(self._blockchain.HeaderHeight, 0)

        self._blockchain.AddBlock(block_one)
        self.assertEqual(self._blockchain.HeaderHeight, 1)

    def test_sys_block_fees(self):

        block_num = 14103
        fee_should_be = 435
