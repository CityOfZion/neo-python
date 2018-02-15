from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.Settings import settings
from neo.Core.Blockchain import Blockchain
from neocore.UInt160 import UInt160
import json
import os
import requests
import tarfile
import logzero
import shutil

from neo.api.REST.NotificationRestApi import NotificationRestApi

from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB
from klein.test.test_resource import requestMock


class NotificationDBTestCase(BlockchainFixtureTestCase):

    N_FIXTURE_REMOTE_LOC = 'https://s3.us-east-2.amazonaws.com/cityofzion/fixtures/notif_fixture_v3.tar.gz'
    N_FIXTURE_FILENAME = './Chains/notif_fixture_v3.tar.gz'
    N_NOTIFICATION_DB_NAME = 'fixtures/test_notifications'

    contract_hash = UInt160(data=bytearray(b'\x11\xc4\xd1\xf4\xfb\xa6\x19\xf2b\x88p\xd3n:\x97s\xe8tp['))
    event_tx = '042e4168cb2d563714d3f35ff76b7efc6c7d428360c97b6b45a18b5b1a4faa40'

    addr_to = 'AHbmRX5sL8oxp4dJZRNg5crCGUGxuMUyRB'
    addr_from = 'AcFnRrVC5emrTEkuFuRPufcuTb6KsAJ3vR'

    app = None  # type:NotificationRestApi

    @classmethod
    def leveldb_testpath(self):
        return './fixtures/test_chain'

    @classmethod
    def setUpClass(cls):

        super(NotificationDBTestCase, cls).setUpClass()

        if not os.path.exists(cls.N_FIXTURE_FILENAME):
            logzero.logger.info(
                "downloading fixture notification database from %s. this may take a while" % cls.N_FIXTURE_REMOTE_LOC)

            response = requests.get(cls.N_FIXTURE_REMOTE_LOC, stream=True)

            response.raise_for_status()
            with open(cls.N_FIXTURE_FILENAME, 'wb+') as handle:
                for block in response.iter_content(1024):
                    handle.write(block)

        try:
            tar = tarfile.open(cls.N_FIXTURE_FILENAME)
            tar.extractall()
            tar.close()
        except Exception as e:
            raise Exception("Could not extract tar file - %s. You may want need to remove the fixtures file %s manually to fix this." % (e, cls.N_FIXTURE_FILENAME))

        if not os.path.exists(cls.N_NOTIFICATION_DB_NAME):
            raise Exception("Error downloading fixtures")

        settings.NOTIFICATION_DB_PATH = cls.N_NOTIFICATION_DB_NAME
        ndb = NotificationDB.instance()
        ndb.start()

    @classmethod
    def tearDownClass(cls):

        super(NotificationDBTestCase, cls).tearDownClass()

        NotificationDB.instance().close()
        shutil.rmtree(cls.N_NOTIFICATION_DB_NAME)

    def setUp(self):
        self.app = NotificationRestApi()

    def test_1_ok(self):

        ndb = NotificationDB.instance()

        events = ndb.get_by_block(627529)

        self.assertEqual(len(events), 1)

    def test_2_klein_app(self):

        self.assertIsNotNone(self.app.notif)

    def test_3_index(self):

        mock_req = requestMock(path=b'/')
        res = self.app.home(mock_req)
        self.assertIn('endpoints', res)

    def test_4_by_block(self):
        mock_req = requestMock(path=b'/block/627529')
        res = self.app.get_by_block(mock_req, 627529)
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 1)
        results = jsn['results']
        self.assertEqual(len(results), 1)

    def test_5_block_no_results(self):
        mock_req = requestMock(path=b'/block/206')
        res = self.app.get_by_block(mock_req, 206)
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 0)
        results = jsn['results']
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)

    def test_6_block_num_too_big(self):
        mock_req = requestMock(path=b'/block/2060200054055066')
        res = self.app.get_by_block(mock_req, 2060200054055066)
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 0)
        results = jsn['results']
        self.assertIsInstance(results, list)
        self.assertIn('Could not get notifications', jsn['message'])

    def test_7_by_addr(self):
        mock_req = requestMock(path=b'/addr/AL5e5ZcqtBTKjcQ8reiePrUBMYSD88v59a')
        res = self.app.get_by_addr(mock_req, 'AL5e5ZcqtBTKjcQ8reiePrUBMYSD88v59a')
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 127)
        results = jsn['results']
        self.assertEqual(len(results), 127)

    def test_8_bad_addr(self):
        mock_req = requestMock(path=b'/addr/AcFnRrVC5emrTEkuFuRPufcuTb6KsAJ3v')
        res = self.app.get_by_addr(mock_req, 'AcFnRrVC5emrTEkuFuRPufcuTb6KsAJ3v')
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 0)
        results = jsn['results']
        self.assertIsInstance(results, list)
        self.assertIn('Could not get notifications', jsn['message'])

    def test_9_by_tx(self):
        mock_req = requestMock(path=b'/tx/0x4c927a7f365cb842ea3576eae474a89183c9e43970a8509b23570a86cb4f5121')
        res = self.app.get_by_tx(mock_req, '0x4c927a7f365cb842ea3576eae474a89183c9e43970a8509b23570a86cb4f5121')
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 1)
        results = jsn['results']
        self.assertEqual(len(results), 1)

    def test_9_by_bad_tx(self):
        mock_req = requestMock(path=b'/tx/2e4168cb2d563714d3f35ff76b7efc6c7d428360c97b6b45a18b5b1a4faa40')
        res = self.app.get_by_tx(mock_req, b'2e4168cb2d563714d3f35ff76b7efc6c7d428360c97b6b45a18b5b1a4faa40')
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 0)
        results = jsn['results']
        self.assertIsInstance(results, list)
        self.assertIn('Could not get tx with hash', jsn['message'])

    def test_get_by_contract(self):
        mock_req = requestMock(path=b'/contract/73d2f26ada9cd95861eed99e43f9aafa05630849')
        res = self.app.get_by_contract(mock_req, '73d2f26ada9cd95861eed99e43f9aafa05630849')
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 4)
        results = jsn['results']
        self.assertEqual(len(results), 4)

    def test_get_by_contract_empty(self):
        mock_req = requestMock(path=b'/contract/a3d2f26ada9cd95861eed99e43f9aafa05630849')
        res = self.app.get_by_contract(mock_req, 'a3d2f26ada9cd95861eed99e43f9aafa05630849')
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 0)
        results = jsn['results']
        self.assertEqual(len(results), 0)

    def test_get_tokens(self):
        mock_req = requestMock(path=b'/tokens')
        res = self.app.get_tokens(mock_req)
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 364)
        results = jsn['results']
        self.assertIsInstance(results, list)

    def test_pagination_for_addr_results(self):
        mock_req = requestMock(path=b'/addr/AFmseVrdL9f9oyCzZefL9tG6UbvhPbdYzM')
        res = self.app.get_by_addr(mock_req, 'AFmseVrdL9f9oyCzZefL9tG6UbvhPbdYzM')
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 1027)
        results = jsn['results']
        self.assertEqual(len(results), 1000)

        mock_req = requestMock(path=b'/addr/AFmseVrdL9f9oyCzZefL9tG6UbvhPbdYzM?page=1')
        res = self.app.get_by_addr(mock_req, 'AFmseVrdL9f9oyCzZefL9tG6UbvhPbdYzM')
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 1027)
        results = jsn['results']
        self.assertEqual(len(results), 27)
