"""
Run only these tests:

    $ python -m unittest neo.api.JSONRPC.test_extended_json_rpc_api
"""
import json
import os
import shutil
from klein.test.test_resource import requestMock
from twisted.web import server
from twisted.web.test.test_web import DummyChannel
from neo.api.JSONRPC.ExtendedJsonRpcApi import ExtendedJsonRpcApi
from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Wallets.utils import to_aes_key
from neo.Blockchain import GetBlockchain
from neo.Settings import settings
from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase


def mock_post_request(body):
    return requestMock(path=b'/', method=b"POST", body=body)


def mock_get_request(path, method=b"GET"):
    request = server.Request(DummyChannel(), False)
    request.uri = path
    request.method = method
    request.clientproto = b'HTTP/1.1'
    return request


class ExtendedJsonRpcApiTestCase(BlockchainFixtureTestCase):
    app = None  # type:JsonRpcApi

    @classmethod
    def leveldb_testpath(self):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    def setUp(self):
        self.app = ExtendedJsonRpcApi(20332)

    def test_HTTP_OPTIONS_request(self):
        mock_req = mock_get_request(b'/?test', b"OPTIONS")
        res = json.loads(self.app.home(mock_req))

        self.assertTrue("GET" in res['supported HTTP methods'])
        self.assertTrue("POST" in res['supported HTTP methods'])
        self.assertTrue("extended-rpc" in res['JSON-RPC server type'])

    def test_invalid_request_method(self):
        # test HEAD method
        mock_req = mock_get_request(b'/?test', b"HEAD")
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["error"]["code"], -32600)
        self.assertEqual(res["error"]["message"], 'HEAD is not a supported HTTP method')

    def test_invalid_json_payload(self):
        # test POST requests
        mock_req = mock_post_request(b"{ invalid")
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["error"]["code"], -32700)

        mock_req = mock_post_request(json.dumps({"some": "stuff"}).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["error"]["code"], -32600)

        # test GET requests
        mock_req = mock_get_request(b"/?%20invalid")  # equivalent to "/? invalid"
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["error"]["code"], -32600)

        mock_req = mock_get_request(b"/?some=stuff")
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["error"]["code"], -32600)

    def _gen_post_rpc_req(self, method, params=None, request_id="2"):
        ret = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method
        }
        if params:
            ret["params"] = params
        return ret

    def _gen_get_rpc_req(self, method, params=None, request="2"):
        ret = "/?jsonrpc=2.0&method=%s&params=[]&id=%s" % (method, request)
        if params:
            ret = "/?jsonrpc=2.0&method=%s&params=%s&id=%s" % (method, params, request)
        return ret.encode('utf-8')

    def test_initial_setup(self):
        self.assertTrue(GetBlockchain().GetBlock(0).Hash.To0xString(), '0x996e37358dc369912041f966f8c5d8d3a8255ba5dcbd3447f8a82b55db869099')

    def test_missing_fields(self):
        # test POST requests
        req = self._gen_post_rpc_req("foo")
        del req["jsonrpc"]
        mock_req = mock_post_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["error"]["code"], -32600)
        self.assertEqual(res["error"]["message"], "Invalid value for 'jsonrpc'")

        req = self._gen_post_rpc_req("foo")
        del req["id"]
        mock_req = mock_post_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["error"]["code"], -32600)
        self.assertEqual(res["error"]["message"], "Field 'id' is missing")

        req = self._gen_post_rpc_req("foo")
        del req["method"]
        mock_req = mock_post_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["error"]["code"], -32600)
        self.assertEqual(res["error"]["message"], "Field 'method' is missing")

        # test GET requests
        mock_req = mock_get_request(b"/?method=foo&id=2")
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["error"]["code"], -32600)
        self.assertEqual(res["error"]["message"], "Invalid value for 'jsonrpc'")

        mock_req = mock_get_request(b"/?jsonrpc=2.0&method=foo")
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["error"]["code"], -32600)
        self.assertEqual(res["error"]["message"], "Field 'id' is missing")

        mock_req = mock_get_request(b"/?jsonrpc=2.0&id=2")
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["error"]["code"], -32600)
        self.assertEqual(res["error"]["message"], "Field 'method' is missing")

    def test_invalid_method(self):
        # test POST requests
        req = self._gen_post_rpc_req("invalid", request_id="42")
        mock_req = mock_post_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["id"], "42")
        self.assertEqual(res["error"]["code"], -32601)
        self.assertEqual(res["error"]["message"], "Method not found")

        # test GET requests
        req = self._gen_get_rpc_req("invalid")
        mock_req = mock_get_request(req)
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["error"]["code"], -32601)
        self.assertEqual(res["error"]["message"], "Method not found")

    def test_get_node_state(self):
        # test POST requests
        req = self._gen_post_rpc_req("getnodestate")
        mock_req = mock_post_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertGreater(res['result']['Progress'][0], 0)
        self.assertGreater(res['result']['Progress'][2], 0)
        self.assertGreater(res['result']['Time elapsed (minutes)'], 0)

        # test GET requests
        req = self._gen_get_rpc_req("getnodestate")
        mock_req = mock_get_request(req)
        res = json.loads(self.app.home(mock_req))
        self.assertGreater(res['result']['Progress'][0], 0)
        self.assertGreater(res['result']['Progress'][2], 0)
        self.assertGreater(res['result']['Time elapsed (minutes)'], 0)

    def test_gettxhistory_no_wallet(self):
        req = self._gen_post_rpc_req("gettxhistory")
        mock_req = mock_post_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -400)
        self.assertEqual(error.get('message', None), "Access denied.")

    def test_gettxhistory(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.app.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        req = self._gen_post_rpc_req("gettxhistory")
        mock_req = mock_post_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        for tx in res['result']:
            self.assertIn('txid', tx.keys())
            self.assertIsNotNone(tx['txid'])
            self.assertIn('block_index', tx.keys())
            self.assertIsNotNone(tx['block_index'])
            self.assertIn('blocktime', tx.keys())
            self.assertIsNotNone(tx['blocktime'])
        self.assertEqual(len(res['result']), 9)
        self.app.wallet.Close()
        self.app.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())
