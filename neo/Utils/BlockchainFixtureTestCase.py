import os
from autologging import logged
import tarfile
import requests

from neo.Utils.NeoTestCase import NeoTestCase
from neo.Implementations.Blockchains.LevelDB.TestLevelDBBlockchain import TestLevelDBBlockchain
from neo.Core.Blockchain import Blockchain


@logged
class BlockchainFixtureTestCase(NeoTestCase):

    FIXTURE_REMOTE_LOC = 'https://s3.us-east-2.amazonaws.com/cityofzion/fixtures/fixtures.tar.gz'
    FIXTURE_FILENAME = './Chains/fixtures.tar.gz'
    _blockchain = None


    @classmethod
    def leveldb_testpath(self):
        return 'Override me!'


    @classmethod
    def setUpClass(self):

        super(BlockchainFixtureTestCase, self).setUpClass()

        if os.path.exists(self.FIXTURE_FILENAME):
            self.__log.debug("fixtures already downloaded")
        else:
            self.__log.debug("downloading fixture block database. this may take a while")
            response = requests.get(self.FIXTURE_REMOTE_LOC, stream=True)
            response.raise_for_status()
            with open(self.FIXTURE_FILENAME, 'wb+') as handle:
                for block in response.iter_content(1024):
                    handle.write(block)

        self.__log.debug("opening tar file")
        try:
            tar = tarfile.open(self.FIXTURE_FILENAME)
            tar.extractall()
            tar.close()
            self.__log.debug("extracted tar file")
        except Exception as e:
            self.__log.debug("Could not extract tar file %s " % e)


        if os.path.exists(self.leveldb_testpath()):
            self.__log.debug('loading blockchain')
            self._blockchain = TestLevelDBBlockchain(path=self.leveldb_testpath())
            Blockchain.RegisterBlockchain(self._blockchain)
            self.__log.debug("Starting Tests")
        else:
            self.__log.debug("Error downloading fixtures")


    @classmethod
    def tearDownClass(self):
        Blockchain.Default().DeregisterBlockchain()
        if self._blockchain is not None:
            self._blockchain.Dispose()
