from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase


class LevelDBTest(BlockchainFixtureTestCase):

    @classmethod
    def leveldb_testpath(self):
        return './fixtures/test_chain'

    def test_a_initial_setup(self):

        self.assertEqual(self._blockchain.Height, 758715)
