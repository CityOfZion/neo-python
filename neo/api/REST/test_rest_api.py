import json
import os

from aiohttp.test_utils import AioHTTPTestCase

from neo.Implementations.Notifications.NotificationDB import NotificationDB
from neo.Settings import settings
from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.api.REST.RestApi import RestApi


class NotificationDBTestCase(BlockchainFixtureTestCase, AioHTTPTestCase):

    def __init__(self, *args, **kwargs):
        super(NotificationDBTestCase, self).__init__(*args, **kwargs)

    async def get_application(self):
        """
        Override the get_app method to return your application.
        """
        self.api_server = RestApi()
        return self.api_server.app

    def do_test_get(self, url, data=None):
        async def test_get_route(url, data=None):
            resp = await self.client.get(url, data=data)
            text = await resp.text()
            return text

        return self.loop.run_until_complete(test_get_route(url, data))

    @classmethod
    def leveldb_testpath(cls):
        super(NotificationDBTestCase, cls).leveldb_testpath()
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    def test_1_ok(self):
        ndb = NotificationDB.instance()

        events = ndb.get_by_block(9583)

        self.assertEqual(len(events), 1)

    def test_2_app_server(self):
        self.assertIsNotNone(self.api_server.notif)

    def test_3_index(self):
        res = self.do_test_get("/")
        self.assertIn('endpoints', res)

    def test_4_by_block(self):
        res = self.do_test_get("/v1/notifications/block/9583")
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 1)
        results = jsn['results']
        self.assertEqual(len(results), 1)

    def test_5_block_no_results(self):
        res = self.do_test_get("/v1/notifications/block/206")
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 0)
        results = jsn['results']
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)

    def test_6_block_num_too_big(self):
        res = self.do_test_get("/v1/notifications/block/2060200054055066")
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 0)
        results = jsn['results']
        self.assertIsInstance(results, type(None))
        self.assertIn('Higher than current block', jsn['message'])

    def test_7_by_addr(self):
        res = self.do_test_get("/v1/notifications/addr/AXpNr3SDfLXbPHNdqxYeHK5cYpKMHZxMZ9")
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 1007)
        results = jsn['results']
        self.assertEqual(len(results), 500)

    def test_8_bad_addr(self):
        res = self.do_test_get("/v1/notifications/addr/AcFnRrVC5emrTEkuFuRPufcuTb6KsAJ3v")
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 0)
        results = jsn['results']
        self.assertIsInstance(results, type(None))
        self.assertIn('Could not get notifications', jsn['message'])

    def test_9_by_tx(self):
        res = self.do_test_get("/v1/notifications/tx/0xa2a37fd2ab7048d70d51eaa8af2815e0e542400329b05a34274771174180a7e8")
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 1)
        results = jsn['results']
        self.assertEqual(len(results), 1)

    def test_9_by_bad_tx(self):
        res = self.do_test_get("/v1/notifications/tx/2e4168cb2d563714d3f35ff76b7efc6c7d428360c97b6b45a18b5b1a4faa40")
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 0)
        results = jsn['results']
        self.assertIsInstance(results, type(None))
        self.assertIn('Could not get tx with hash', jsn['message'])

    def test_get_by_contract(self):
        res = self.do_test_get("/v1/notifications/contract/b9fbcff6e50fd381160b822207231233dd3c56c2")
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 1006)
        results = jsn['results']
        self.assertEqual(len(results), 500)

    def test_get_by_contract_empty(self):
        res = self.do_test_get("/v1/notifications/contract/910cba960880c75072d0c625dfff459f72aae047")
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 0)
        results = jsn['results']
        self.assertEqual(len(results), 0)

    def test_get_tokens(self):
        res = self.do_test_get("/v1/tokens")
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 5)
        results = jsn['results']
        self.assertIsInstance(results, list)

    def test_pagination_for_addr_results(self):
        res = self.do_test_get("/v1/notifications/addr/AXpNr3SDfLXbPHNdqxYeHK5cYpKMHZxMZ9")
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 1007)
        results = jsn['results']
        self.assertEqual(len(results), 500)
        self.assertEqual(jsn['total_pages'], 3)

        res = self.do_test_get("/v1/notifications/addr/AXpNr3SDfLXbPHNdqxYeHK5cYpKMHZxMZ9?page=1")
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 1007)
        results = jsn['results']
        self.assertEqual(len(results), 500)

        res = self.do_test_get("/v1/notifications/addr/AXpNr3SDfLXbPHNdqxYeHK5cYpKMHZxMZ9?page=2")
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 1007)
        results = jsn['results']
        self.assertEqual(len(results), 500)

        res = self.do_test_get("/v1/notifications/addr/AXpNr3SDfLXbPHNdqxYeHK5cYpKMHZxMZ9?page=3")
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 1007)
        results = jsn['results']
        self.assertEqual(len(results), 7)

    def test_pagination_page_size_for_addr_results(self):
        res = self.do_test_get("/v1/notifications/addr/AXpNr3SDfLXbPHNdqxYeHK5cYpKMHZxMZ9?pagesize=100")
        jsn = json.loads(res)
        self.assertEqual(jsn['total'], 1007)
        results = jsn['results']
        self.assertEqual(len(results), 100)
        self.assertEqual(jsn['total_pages'], 11)

        res = self.do_test_get("/v1/notifications/addr/AXpNr3SDfLXbPHNdqxYeHK5cYpKMHZxMZ9?pagesize=100&page=11")
        jsn = json.loads(res)
        results = jsn['results']
        self.assertEqual(len(results), 7)

    def test_status(self):
        res = self.do_test_get("/v1/status")
        jsn = json.loads(res)
        self.assertEqual(12356, jsn['current_height'])
        self.assertEqual(settings.VERSION_NAME, jsn['version'])
        self.assertEqual(0, jsn['num_peers'])

    def test_get_token(self):
        res = self.do_test_get("/v1/token/b9fbcff6e50fd381160b822207231233dd3c56c2")
        jsn = json.loads(res)
        result = jsn['results'][0]
        self.assertEqual(9479, result['block'])
        self.assertEqual("NXT2", result['token']['symbol'])
