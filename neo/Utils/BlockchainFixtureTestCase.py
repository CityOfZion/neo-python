from neo.Implementations.Blockchains.LevelDB.TestLevelDBBlockchain import TestLevelDBBlockchain
from neo.Core.Blockchain import Blockchain

import unittest
import tarfile
import requests
import os

class BlockchainFixtureTestCase(unittest.TestCase):

    FIXTURE_REMOTE_LOC = 'https://s3.us-east-2.amazonaws.com/cityofzion/fixtures/fixtures.tar.gz'
    FIXTURE_FILENAME = './Chains/fixtures.tar.gz'
    _blockchain = None


    @classmethod
    def leveldb_testpath(self):
        return 'Override Me!'


    @classmethod
    def setUpClass(self):

        if os.path.exists(self.leveldb_testpath()):
            print("fixtures already downloaded")

        else:

            print("downloading fixture block database. this may take a while")

            response = requests.get(self.FIXTURE_REMOTE_LOC, stream=True)

            response.raise_for_status()
            with open(self.FIXTURE_FILENAME,'wb+') as handle:
                for block in response.iter_content(1024):
                    handle.write(block)

            print("opening tar file")
            try:
                tar = tarfile.open(self.FIXTURE_FILENAME)
                tar.extractall()
                tar.close()
                print("closing tar file")
            except Exception as e:
                print("Could not extract tar file %s " % e)


        if os.path.exists(self.leveldb_testpath()):
            print('loading blockchain')
            self._blockchain = TestLevelDBBlockchain(path=self.leveldb_testpath())
            Blockchain.RegisterBlockchain(self._blockchain)
            print("Starting Tests")
        else:
            print("Error downloading fixtures")


    @classmethod
    def tearDownClass(self):
        Blockchain.Default().DeregisterBlockchain()
        if self._blockchain is not None:
            self._blockchain.Dispose()
