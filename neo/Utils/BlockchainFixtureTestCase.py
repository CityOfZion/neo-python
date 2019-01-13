import tarfile
import requests
import shutil
import os
import neo
from neo.Utils.NeoTestCase import NeoTestCase
from neo.Implementations.Blockchains.LevelDB.TestLevelDBBlockchain import TestLevelDBBlockchain
from neo.Core.Blockchain import Blockchain
from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB
from neo.Settings import settings
from neo.logging import log_manager
from neo.Network.NodeLeader import NodeLeader

logger = log_manager.getLogger()


class BlockchainFixtureTestCase(NeoTestCase):
    FIXTURE_REMOTE_LOC = 'https://s3.us-east-2.amazonaws.com/cityofzion/fixtures/fixtures_v8.tar.gz'
    FIXTURE_FILENAME = os.path.join(settings.DATA_DIR_PATH, 'Chains/fixtures_v8.tar.gz')

    N_FIXTURE_REMOTE_LOC = 'https://s3.us-east-2.amazonaws.com/cityofzion/fixtures/notif_fixtures_v8.tar.gz'
    N_FIXTURE_FILENAME = os.path.join(settings.DATA_DIR_PATH, 'Chains/notif_fixtures_v8.tar.gz')
    N_NOTIFICATION_DB_NAME = os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_notifications')

    _blockchain = None

    wallets_folder = os.path.dirname(neo.__file__) + '/Utils/fixtures/'

    @classmethod
    def leveldb_testpath(cls):
        return 'Override Me!'

    @classmethod
    def setUpClass(cls):

        Blockchain.DeregisterBlockchain()

        super(BlockchainFixtureTestCase, cls).setUpClass()

        NodeLeader.Instance().Reset()
        NodeLeader.Instance().Setup()

        # setup Blockchain DB
        if not os.path.exists(cls.FIXTURE_FILENAME):
            logger.info(
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
            raise Exception(
                "Could not extract tar file - %s. You may want need to remove the fixtures file %s manually to fix this." % (e, cls.FIXTURE_FILENAME))

        if not os.path.exists(cls.leveldb_testpath()):
            raise Exception("Error downloading fixtures at %s" % cls.leveldb_testpath())

        settings.setup_unittest_net()

        cls._blockchain = TestLevelDBBlockchain(path=cls.leveldb_testpath(), skip_version_check=True)
        Blockchain.RegisterBlockchain(cls._blockchain)

        # setup Notification DB
        if not os.path.exists(cls.N_FIXTURE_FILENAME):
            logger.info(
                "downloading fixture notification database from %s. this may take a while" % cls.N_FIXTURE_REMOTE_LOC)

            response = requests.get(cls.N_FIXTURE_REMOTE_LOC, stream=True)

            response.raise_for_status()
            with open(cls.N_FIXTURE_FILENAME, 'wb+') as handle:
                for block in response.iter_content(1024):
                    handle.write(block)

        try:
            tar = tarfile.open(cls.N_FIXTURE_FILENAME)
            tar.extractall(path=settings.DATA_DIR_PATH)
            tar.close()

        except Exception as e:
            raise Exception(
                "Could not extract tar file - %s. You may want need to remove the fixtures file %s manually to fix this." % (e, cls.N_FIXTURE_FILENAME))
        if not os.path.exists(cls.N_NOTIFICATION_DB_NAME):
            raise Exception("Error downloading fixtures at %s" % cls.N_NOTIFICATION_DB_NAME)

        settings.NOTIFICATION_DB_PATH = cls.N_NOTIFICATION_DB_NAME
        ndb = NotificationDB.instance()
        ndb.start()

    @classmethod
    def tearDownClass(cls):
        # tear down Blockchain DB
        Blockchain.Default().DeregisterBlockchain()
        if cls._blockchain is not None:
            cls._blockchain.Dispose()

        shutil.rmtree(cls.leveldb_testpath())

        # tear down Notification DB
        NotificationDB.instance().close()
        shutil.rmtree(cls.N_NOTIFICATION_DB_NAME)
