from unittest import TestCase
from neo.Settings import settings
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


class NotificationDBTestCase(TestCase):

    FIXTURE_REMOTE_LOC = 'https://s3.us-east-2.amazonaws.com/cityofzion/fixtures/notif_fixture.tar.gz'
    FIXTURE_FILENAME = './Chains/notif_fixture.tar.gz'
    NOTIFICATION_DB_NAME = 'fixtures/test_notifications'

    contract_hash = UInt160(data=bytearray(b'\x11\xc4\xd1\xf4\xfb\xa6\x19\xf2b\x88p\xd3n:\x97s\xe8tp['))
    event_tx = '042e4168cb2d563714d3f35ff76b7efc6c7d428360c97b6b45a18b5b1a4faa40'

    addr_to = 'AHbmRX5sL8oxp4dJZRNg5crCGUGxuMUyRB'
    addr_from = 'AcFnRrVC5emrTEkuFuRPufcuTb6KsAJ3vR'

    app = None  # type:NotificationRestApi

    @classmethod
    def setUpClass(cls):

        if not os.path.exists(cls.FIXTURE_FILENAME):
            logzero.logger.info(
                "downloading fixture notification database from %s. this may take a while" % cls.FIXTURE_REMOTE_LOC)

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

        if not os.path.exists(cls.NOTIFICATION_DB_NAME):
            raise Exception("Error downloading fixtures")

        settings.NOTIFICATION_DB_PATH = cls.NOTIFICATION_DB_NAME
        ndb = NotificationDB.instance()
        ndb.start()

    @classmethod
    def tearDownClass(cls):
        NotificationDB.instance().close()
        shutil.rmtree(cls.NOTIFICATION_DB_NAME)

    def setUp(self):
        self.app = NotificationRestApi()

    def test_1_ok(self):

        ndb = NotificationDB.instance()

        events = ndb.get_by_block(206939)

        self.assertEqual(len(events), 1)

    def test_2_klein_app(self):

        self.assertIsNotNone(self.app.notif)

    def test_3_index(self):

        mock_req = requestMock(path=b'/')
        res = self.app.home(mock_req)
        self.assertIn('endpoints', res)

    def test_4_by_block(self):
        mock_req = requestMock(path=b'/block/206939')
        res = self.app.get_by_block(mock_req, 206939)
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
        mock_req = requestMock(path=b'/addr/AcFnRrVC5emrTEkuFuRPufcuTb6KsAJ3vR')
        res = self.app.get_by_addr(mock_req, 'AcFnRrVC5emrTEkuFuRPufcuTb6KsAJ3vR')
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 3)
        results = jsn['results']
        self.assertEqual(len(results), 3)

    def test_8_bad_addr(self):
        mock_req = requestMock(path=b'/addr/AcFnRrVC5emrTEkuFuRPufcuTb6KsAJ3v')
        res = self.app.get_by_addr(mock_req, 'AcFnRrVC5emrTEkuFuRPufcuTb6KsAJ3v')
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 0)
        results = jsn['results']
        self.assertIsInstance(results, list)
        self.assertIn('Could not get notifications', jsn['message'])

    # this following test doesn't work because we'd have to load in the blockchain that matches these notifications

#    def test_9_by_tx(self):
#        mock_req = requestMock(path=b'/tx/042e4168cb2d563714d3f35ff76b7efc6c7d428360c97b6b45a18b5b1a4faa40')
#        res = self.app.get_by_tx(mock_req,b'042e4168cb2d563714d3f35ff76b7efc6c7d428360c97b6b45a18b5b1a4faa40')
#        jsn = json.loads(res)
#        print("JSON %s " % jsn)
#        self.assertEqual(jsn['total'],1)
#        results = jsn['results']
#        self.assertEqual(len(results), 1)

    def test_9_by_bad_tx(self):
        mock_req = requestMock(path=b'/tx/2e4168cb2d563714d3f35ff76b7efc6c7d428360c97b6b45a18b5b1a4faa40')
        res = self.app.get_by_tx(mock_req, b'2e4168cb2d563714d3f35ff76b7efc6c7d428360c97b6b45a18b5b1a4faa40')
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 0)
        results = jsn['results']
        self.assertIsInstance(results, list)
        self.assertIn('Could not get tx with hash', jsn['message'])
