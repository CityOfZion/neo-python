from unittest import TestCase
from neo.Settings import settings
from neo.SmartContract.SmartContractEvent import SmartContractEvent, NotifyEvent
from neocore.UInt160 import UInt160
from neocore.UInt256 import UInt256
from uuid import uuid1
import shutil
import json
from neo.Implementations.Notifications.REST.NotificationServer import NotificationServer

from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB
from klein.test.test_resource import requestMock


class NotificationDBTestCase(TestCase):

    contract_hash = UInt160(data=bytearray(b'\x11\xc4\xd1\xf4\xfb\xa6\x19\xf2b\x88p\xd3n:\x97s\xe8tp['))
    event_tx = '042e4168cb2d563714d3f35ff76b7efc6c7d428360c97b6b45a18b5b1a4faa40'

    addr_to = 'AHbmRX5sL8oxp4dJZRNg5crCGUGxuMUyRB'
    addr_from = 'AcFnRrVC5emrTEkuFuRPufcuTb6KsAJ3vR'

    app = None  # type:NotificationServer

    @classmethod
    def setUpClass(cls):

        settings.NOTIFICATION_DB_PATH = 'fixtures/test_notifications'
        ndb = NotificationDB.instance()
        ndb.start()

    @classmethod
    def tearDownClass(cls):
        NotificationDB.instance().close()

    def setUp(self):
        self.app = NotificationServer()

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
