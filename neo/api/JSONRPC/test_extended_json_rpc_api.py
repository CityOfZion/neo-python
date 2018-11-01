"""
Run only these tests:

    $ python -m unittest neo.api.JSONRPC.test_extended_json_rpc_api
"""
import json
import os
import shutil
from klein.test.test_resource import requestMock
from neo.api.JSONRPC.ExtendedJsonRpcApi import ExtendedJsonRpcApi
from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Wallets.utils import to_aes_key
from neo.Blockchain import GetBlockchain
from neo.Settings import settings
from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase


def mock_request(body):
    return requestMock(path=b'/', method="POST", body=body)


class ExtendedJsonRpcApiTestCase(BlockchainFixtureTestCase):
    app = None  # type:JsonRpcApi

    @classmethod
    def leveldb_testpath(self):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    def setUp(self):
        self.app = ExtendedJsonRpcApi(20332)

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

    def test_initial_setup(self):
        self.assertTrue(GetBlockchain().GetBlock(0).Hash.To0xString(), '0x996e37358dc369912041f966f8c5d8d3a8255ba5dcbd3447f8a82b55db869099')

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
        self.assertEqual(res["error"]["message"], "Method not found")

    def test_get_node_state(self):
        req = self._gen_rpc_req("getnodestate")
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertGreater(res['result']['Progress'][0], 0)
        self.assertGreater(res['result']['Progress'][2], 0)
        self.assertGreater(res['result']['Time elapsed (minutes)'], 0)

    def test_gettxhistory_no_wallet(self):
        req = self._gen_rpc_req("gettxhistory")
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
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
        req = self._gen_rpc_req("gettxhistory")
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
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
