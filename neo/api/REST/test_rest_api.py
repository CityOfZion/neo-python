from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.Settings import settings
import json
import os
import requests
import tarfile
import shutil

from neo.api.REST.RestApi import RestApi

from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB
from klein.test.test_resource import requestMock


class NotificationDBTestCase(BlockchainFixtureTestCase):
    app = None  # type:RestApi

    @classmethod
    def leveldb_testpath(cls):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    def setUp(self):
        self.app = RestApi()

    def test_1_ok(self):

        ndb = NotificationDB.instance()

        events = ndb.get_by_block(9583)

        self.assertEqual(len(events), 1)

    def test_2_klein_app(self):

        self.assertIsNotNone(self.app.notif)

    def test_3_index(self):

        mock_req = requestMock(path=b'/')
        res = self.app.home(mock_req)
        self.assertIn('endpoints', res)

    def test_4_by_block(self):
        mock_req = requestMock(path=b'/block/9583')
        res = self.app.get_by_block(mock_req, 9583)
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
        self.assertIsInstance(results, type(None))
        self.assertIn('Higher than current block', jsn['message'])

    def test_7_by_addr(self):
        mock_req = requestMock(path=b'/addr/AXpNr3SDfLXbPHNdqxYeHK5cYpKMHZxMZ9')
        res = self.app.get_by_addr(mock_req, 'AXpNr3SDfLXbPHNdqxYeHK5cYpKMHZxMZ9')
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 1007)
        results = jsn['results']
        self.assertEqual(len(results), 500)

    def test_8_bad_addr(self):
        mock_req = requestMock(path=b'/addr/AcFnRrVC5emrTEkuFuRPufcuTb6KsAJ3v')
        res = self.app.get_by_addr(mock_req, 'AcFnRrVC5emrTEkuFuRPufcuTb6KsAJ3v')
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 0)
        results = jsn['results']
        self.assertIsInstance(results, type(None))
        self.assertIn('Could not get notifications', jsn['message'])

    def test_9_by_tx(self):
        mock_req = requestMock(path=b'/tx/0xa2a37fd2ab7048d70d51eaa8af2815e0e542400329b05a34274771174180a7e8')
        res = self.app.get_by_tx(mock_req, '0xa2a37fd2ab7048d70d51eaa8af2815e0e542400329b05a34274771174180a7e8')
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
        self.assertIsInstance(results, type(None))
        self.assertIn('Could not get tx with hash', jsn['message'])

    def test_get_by_contract(self):
        mock_req = requestMock(path=b'/contract/b9fbcff6e50fd381160b822207231233dd3c56c2')
        res = self.app.get_by_contract(mock_req, 'b9fbcff6e50fd381160b822207231233dd3c56c2')
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 1006)
        results = jsn['results']
        self.assertEqual(len(results), 500)

    def test_get_by_contract_empty(self):
        mock_req = requestMock(path=b'/contract/910cba960880c75072d0c625dfff459f72aae047')
        res = self.app.get_by_contract(mock_req, '910cba960880c75072d0c625dfff459f72aae047')
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 0)
        results = jsn['results']
        self.assertEqual(len(results), 0)

    def test_get_tokens(self):
        mock_req = requestMock(path=b'/tokens')
        res = self.app.get_tokens(mock_req)
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 5)
        results = jsn['results']
        self.assertIsInstance(results, list)

    def test_pagination_for_addr_results(self):
        mock_req = requestMock(path=b'/addr/AXpNr3SDfLXbPHNdqxYeHK5cYpKMHZxMZ9')
        res = self.app.get_by_addr(mock_req, 'AXpNr3SDfLXbPHNdqxYeHK5cYpKMHZxMZ9')
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 1007)
        results = jsn['results']
        self.assertEqual(len(results), 500)
        self.assertEqual(jsn['total_pages'], 3)

        mock_req = requestMock(path=b'/addr/AXpNr3SDfLXbPHNdqxYeHK5cYpKMHZxMZ9?page=1')
        res = self.app.get_by_addr(mock_req, 'AXpNr3SDfLXbPHNdqxYeHK5cYpKMHZxMZ9')
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 1007)
        results = jsn['results']
        self.assertEqual(len(results), 500)

        mock_req = requestMock(path=b'/addr/AXpNr3SDfLXbPHNdqxYeHK5cYpKMHZxMZ9?page=2')
        res = self.app.get_by_addr(mock_req, 'AXpNr3SDfLXbPHNdqxYeHK5cYpKMHZxMZ9')
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 1007)
        results = jsn['results']
        self.assertEqual(len(results), 500)

        mock_req = requestMock(path=b'/addr/AXpNr3SDfLXbPHNdqxYeHK5cYpKMHZxMZ9?page=3')
        res = self.app.get_by_addr(mock_req, 'AXpNr3SDfLXbPHNdqxYeHK5cYpKMHZxMZ9')
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 1007)
        results = jsn['results']
        self.assertEqual(len(results), 7)

    def test_pagination_page_size_for_addr_results(self):
        mock_req = requestMock(path=b'/addr/AXpNr3SDfLXbPHNdqxYeHK5cYpKMHZxMZ9?pagesize=100')
        res = self.app.get_by_addr(mock_req, 'AXpNr3SDfLXbPHNdqxYeHK5cYpKMHZxMZ9')
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 1007)
        results = jsn['results']
        self.assertEqual(len(results), 100)
        self.assertEqual(jsn['total_pages'], 11)

        mock_req = requestMock(path=b'/addr/AXpNr3SDfLXbPHNdqxYeHK5cYpKMHZxMZ9?pagesize=100&page=11')
        res = self.app.get_by_addr(mock_req, 'AXpNr3SDfLXbPHNdqxYeHK5cYpKMHZxMZ9')
        jsn = json.loads(res)
        results = jsn['results']
        self.assertEqual(len(results), 7)

    def test_block_heigher_than_current(self):
        mock_req = requestMock(path=b'/block/8000000')
        res = self.app.get_by_block(mock_req, 800000)
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 0)
        results = jsn['results']
        self.assertIsInstance(results, type(None))
        self.assertIn('Higher than current block', jsn['message'])
