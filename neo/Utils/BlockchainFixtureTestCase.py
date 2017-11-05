from neo.Utils.NeoTestCase import NeoTestCase
from neo.Implementations.Blockchains.LevelDB.TestLevelDBBlockchain import TestLevelDBBlockchain

from neo.Core.Blockchain import Blockchain

import tarfile
import requests
import os
from autologging import logged
import shutil
import time


@logged
class BlockchainFixtureTestCase(NeoTestCase):

    FIXTURE_REMOTE_LOC = 'https://s3.us-east-2.amazonaws.com/cityofzion/fixtures/fixtures_v2.tar.gz'
    FIXTURE_FILENAME = './Chains/fixtures_v2.tar.gz'
    _blockchain = None

    @classmethod
    def leveldb_testpath(cls):
        return 'Override Me!'

    @classmethod
    def setUpClass(cls):

        Blockchain.DeregisterBlockchain()

        super(BlockchainFixtureTestCase, cls).setUpClass()

        if not os.path.exists(cls.FIXTURE_FILENAME):

            print("downloading fixture block database. this may take a while")

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
            print("Could not extract tar file %s " % e)

        if os.path.exists(cls.leveldb_testpath()):
            cls._blockchain = TestLevelDBBlockchain(path=cls.leveldb_testpath())

            Blockchain.RegisterBlockchain(cls._blockchain)
        else:
            print("Error downloading fixtures")

    @classmethod
    def tearDownClass(cls):

        Blockchain.Default().DeregisterBlockchain()
        if cls._blockchain is not None:
            cls._blockchain.Dispose()

        shutil.rmtree(cls.leveldb_testpath())
