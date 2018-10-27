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

    wallet_1_addr = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'

    watch_addr_str = 'AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEm'

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

    def test_transfer_tokens_good(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.app.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        req = self._gen_rpc_req("transfertokens", params=["NXT4", self.wallet_1_addr, self.watch_addr_str, 1])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))

        self.assertEqual(res['result']['type'], "InvocationTransaction")
        self.assertEqual(res['result']['vout'][0]['address'], self.wallet_1_addr)
        self.assertEqual(res['result']['net_fee'], "0.0001")

        self.app.wallet.Close()
        self.app.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_transfer_tokens_no_wallet(self):
        req = self._gen_rpc_req("transfertokens", params=["NXT4", self.wallet_1_addr, self.watch_addr_str, 1])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))

        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -400)
        self.assertEqual(error.get('message', None), "Access denied.")

    def test_transfer_tokens_bad_args(self):  # too few args
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.app.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        req = self._gen_rpc_req("transfertokens", params=["NXT4", self.wallet_1_addr, self.watch_addr_str])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))

        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")

        self.app.wallet.Close()
        self.app.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_transfer_tokens_bad_token(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.app.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        req = self._gen_rpc_req("transfertokens", params=["Blah", self.wallet_1_addr, self.watch_addr_str, 1])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))

        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")

        self.app.wallet.Close()
        self.app.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_transfer_tokens_bad_from_addr(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.app.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        req = self._gen_rpc_req("transfertokens", params=["NXT4", "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc", self.watch_addr_str, 1])  # address is too short
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))

        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32603)
        self.assertEqual(error.get('message', None), "Not correct Address, wrong length.")

        self.app.wallet.Close()
        self.app.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_transfer_tokens_bad_to_addr(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.app.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        req = self._gen_rpc_req("transfertokens", params=["NXT4", self.wallet_1_addr, "AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkE", 1])  # address is too short
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))

        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")

        self.app.wallet.Close()
        self.app.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_transfer_tokens_insufficient_funds(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.app.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )

        token = list(self.app.wallet.GetTokens().values())[0]
        balance = self.app.wallet.GetBalance(token)

        req = self._gen_rpc_req("transfertokens", params=["NXT4", self.wallet_1_addr, self.watch_addr_str, int(balance) + 1])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))

        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -300)
        self.assertEqual(error.get('message', None), "Insufficient funds")

        self.app.wallet.Close()
        self.app.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_transfer_tokens_weird_amount(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.app.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        req = self._gen_rpc_req("transfertokens", params=["NXT4", self.wallet_1_addr, self.watch_addr_str, "blah"])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))

        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32603)
        self.assertEqual(error.get('message', None), "[<class 'decimal.ConversionSyntax'>]")

        self.app.wallet.Close()
        self.app.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())
