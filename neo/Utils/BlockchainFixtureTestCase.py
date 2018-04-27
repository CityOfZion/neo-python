import tarfile
import requests
import shutil

from neo.Settings import settings
from neo.Utils.NeoTestCase import NeoTestCase
from neo.Implementations.Blockchains.LevelDB.TestLevelDBBlockchain import TestLevelDBBlockchain
from neo.Core.Blockchain import Blockchain
import logzero
import os


class BlockchainFixtureTestCase(NeoTestCase):
    FIXTURE_REMOTE_LOC = 'https://s3.us-east-2.amazonaws.com/cityofzion/fixtures/fixtures_v7.tar.gz'
    FIXTURE_FILENAME = os.path.join(settings.DATA_DIR_PATH, 'Chains/fixtures_v7.tar.gz')
    _blockchain = None

    @classmethod
    def leveldb_testpath(cls):
        return 'Override Me!'

    @classmethod
    def setUpClass(cls):

        Blockchain.DeregisterBlockchain()

        super(BlockchainFixtureTestCase, cls).setUpClass()

        if not os.path.exists(cls.FIXTURE_FILENAME):
            logzero.logger.info(
                "downloading fixture block database from %s. this may take a while" % cls.FIXTURE_REMOTE_LOC)

            response = requests.get(cls.FIXTURE_REMOTE_LOC, stream=True)

            response.raise_for_status()
            os.makedirs(os.path.dirname(cls.FIXTURE_FILENAME), exist_ok=True)
            with open(cls.FIXTURE_FILENAME, 'wb+') as handle:
                for block in response.iter_content(1024):
                    handle.write(block)

        try:
            tar = tarfile.open(cls.FIXTURE_FILENAME)
            tar.extractall(path=settings.DATA_DIR_PATH)
            tar.close()
        except Exception as e:
            raise Exception("Could not extract tar file - %s. You may want need to remove the fixtures file %s manually to fix this." % (e, cls.FIXTURE_FILENAME))

        if not os.path.exists(cls.leveldb_testpath()):
            raise Exception("Error downloading fixtures at %s" % cls.leveldb_testpath())

        cls._blockchain = TestLevelDBBlockchain(path=cls.leveldb_testpath(), skip_version_check=True)
        Blockchain.RegisterBlockchain(cls._blockchain)

    @classmethod
    def tearDownClass(cls):

        Blockchain.Default().DeregisterBlockchain()
        if cls._blockchain is not None:
            cls._blockchain.Dispose()

        shutil.rmtree(cls.leveldb_testpath())
