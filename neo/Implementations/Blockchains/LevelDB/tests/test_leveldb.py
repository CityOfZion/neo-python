from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.Settings import settings
import os


class LevelDBTest(BlockchainFixtureTestCase):

    @classmethod
    def leveldb_testpath(self):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    def test_a_initial_setup(self):
        self.assertEqual(self._blockchain.Height, 758986)
