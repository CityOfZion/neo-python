"""
python -m unittest neo.api.JSONRPC.test_json_rpc_api
"""
import json
from klein.test.test_resource import requestMock
from neo.api.JSONRPC.JsonRpcApi import JsonRpcApi
from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase


def mock_request(body):
    return requestMock(path=b'/', method="POST", body=body)


class JsonRpcApiTestCase(BlockchainFixtureTestCase):
    app = None  # type:JsonRpcApi

    @classmethod
    def leveldb_testpath(self):
        return './fixtures/test_chain'

    def setUp(self):
        self.app = JsonRpcApi()

    def test_invalid_json_payload(self):
        mock_req = mock_request(b"{ invalid")
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["error"]["code"], -32700)

        mock_req = mock_request(json.dumps({"some": "stuff"}).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["error"]["code"], -32600)

    def _gen_rpc_req(self, method, params=None, request_id="2"):
        ret = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method
        }
        if params:
            ret["params"] = params
        return ret

    def test_missing_fields(self):
        req = self._gen_rpc_req("foo")
        del req["jsonrpc"]
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["error"]["code"], -32600)

        req = self._gen_rpc_req("foo")
        del req["id"]
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["error"]["code"], -32600)

        req = self._gen_rpc_req("foo")
        del req["method"]
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["error"]["code"], -32600)

    def test_invalid_method(self):
        req = self._gen_rpc_req("invalid", request_id="42")
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["id"], "42")
        self.assertEqual(res["error"]["code"], -32601)

    def test_getblockcount(self):
        req = self._gen_rpc_req("getblockcount")
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(756620, res["result"])

    def test_getblockhash(self):
        req = self._gen_rpc_req("getblockhash", params='[2]')
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))

        # taken from neoscan
        expected_blockhash = '60ad7aebdae37f1cad7a15b841363b5a7da9fd36bf689cfde75c26c0fa085b64'
        self.assertEqual(expected_blockhash, res["result"])
