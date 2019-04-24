from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.Settings import settings
import os


class LevelDBTest(BlockchainFixtureTestCase):

    @classmethod
    def leveldb_testpath(cls):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    # test need to be updated whenever we change the fixtures
    def test_a_initial_setup(self):
        self.assertEqual(self._blockchain.Height, 12349)
