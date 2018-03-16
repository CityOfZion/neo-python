import tarfile
import requests
import os
import shutil
import time

from neo.Settings import settings
from neo.Utils.NeoTestCase import NeoTestCase
from neo.Implementations.Blockchains.LevelDB.TestLevelDBBlockchain import TestLevelDBBlockchain
from neo.Core.Blockchain import Blockchain
import logzero


class BlockchainFixtureTestCase(NeoTestCase):

    FIXTURE_REMOTE_LOC = 'https://s3.us-east-2.amazonaws.com/cityofzion/fixtures/fixtures_v5.tar.gz'
    FIXTURE_FILENAME = './Chains/fixtures_v5.tar.gz'
    _blockchain = None

    @classmethod
    def leveldb_testpath(cls):
        return 'Override Me!'

    @classmethod
    def setUpClass(cls):

        settings.set_data_dir('.')

        Blockchain.DeregisterBlockchain()

        super(BlockchainFixtureTestCase, cls).setUpClass()

        if not os.path.exists(cls.FIXTURE_FILENAME):
            logzero.logger.info(
                "downloading fixture block database from %s. this may take a while" % cls.FIXTURE_REMOTE_LOC)

            response = requests.get(cls.FIXTURE_REMOTE_LOC, stream=True)

            response.raise_for_status()
            with open(cls.FIXTURE_FILENAME, 'wb+') as handle:
                for block in response.iter_content(1024):
                    handle.write(block)

        try:
            tar = tarfile.open(cls.FIXTURE_FILENAME)
            tar.extractall()
            tar.close()
        except Exception as e:
            raise Exception("Could not extract tar file - %s. You may want need to remove the fixtures file %s manually to fix this." % (e, cls.FIXTURE_FILENAME))

        if not os.path.exists(cls.leveldb_testpath()):
            raise Exception("Error downloading fixtures at %s %s" % (os.getcwd(), cls.leveldb_testpath()))

        cls._blockchain = TestLevelDBBlockchain(path=cls.leveldb_testpath())
        Blockchain.RegisterBlockchain(cls._blockchain)

    @classmethod
    def tearDownClass(cls):

        Blockchain.Default().DeregisterBlockchain()
        if cls._blockchain is not None:
            cls._blockchain.Dispose()

        shutil.rmtree(cls.leveldb_testpath())
