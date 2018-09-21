from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.Settings import settings
import os


class LevelDBBlockchainTest(BlockchainFixtureTestCase):
    @classmethod
    def leveldb_testpath(self):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    # test need to be updated whenever we change the fixtures
    def test_01_initial_setup(self):
        self.assertEqual(self._blockchain.Height, 12349)

    def test_02_GetBlockHash(self):
        # test requested block height exceeding blockchain current_height
        invalid_bc_height = self._blockchain.Height + 1
        result = self._blockchain.GetBlockHash(invalid_bc_height)
        self.assertEqual(result, None)

        # test header index length mismatch
        # save index to restore later
        saved = self._blockchain._header_index
        self._blockchain._header_index = self._blockchain._header_index[:10]
        result = self._blockchain.GetBlockHash(100)
        self.assertEqual(result, None)
        self._blockchain._header_index = saved

        # finally test correct retrieval
        result = self._blockchain.GetBlockHash(100)
        self.assertEqual(result, self._blockchain._header_index[100])

    def test_03_GetBlockByHeight(self):
        # test correct retrieval
        block = self._blockchain.GetBlockByHeight(100)
        self.assertEqual(block.GetHashCode().ToString(), self._blockchain.GetBlockHash(100).decode('utf-8'))

        # and also a invalid retrieval
        invalid_bc_height = self._blockchain.Height + 1
        block = self._blockchain.GetBlockByHeight(invalid_bc_height)
        self.assertEqual(block, None)
