"""
Run only thse tests:

    $ python -m unittest neo.api.JSONRPC.test_json_rpc_api
"""
import json
import pprint
from klein.test.test_resource import requestMock

from neo import __version__
from neo.api.JSONRPC.JsonRpcApi import JsonRpcApi
from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.IO.Helper import Helper
from neocore.UInt160 import UInt160
import binascii


def mock_request(body):
    return requestMock(path=b'/', method="POST", body=body)


class JsonRpcApiTestCase(BlockchainFixtureTestCase):
    app = None  # type:JsonRpcApi

    @classmethod
    def leveldb_testpath(self):
        return './fixtures/test_chain'

    def setUp(self):
        self.app = JsonRpcApi(20332)

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
        self.assertEqual(res["error"]["message"], "Method not found")

    def test_getblockcount(self):
        req = self._gen_rpc_req("getblockcount")
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(756620, res["result"])

    def test_getblockhash(self):
        req = self._gen_rpc_req("getblockhash", params=[2])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))

        # taken from neoscan
        expected_blockhash = '0x60ad7aebdae37f1cad7a15b841363b5a7da9fd36bf689cfde75c26c0fa085b64'
        self.assertEqual(expected_blockhash, res["result"])

    def test_getblockhash_failure(self):
        req = self._gen_rpc_req("getblockhash", params=[-1])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(-100, res["error"]["code"])
        self.assertEqual("Invalid Height", res["error"]["message"])

    def test_account_state(self):
        addr_str = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
        req = self._gen_rpc_req("getaccountstate", params=[addr_str])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result']['balances']['0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b'], '4061.0')
        self.assertEqual(res['result']['script_hash'], addr_str)

    def test_account_state_not_existing_yet(self):
        addr_str = 'AHozf8x8GmyLnNv8ikQcPKgRHQTbFi46u2'
        req = self._gen_rpc_req("getaccountstate", params=[addr_str])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result']['balances'], {})
        self.assertEqual(res['result']['script_hash'], addr_str)

    def test_account_state_failure(self):
        addr_str = 'Axozf8x8GmyLnNv8ikQcPKgRHQTbFi46u2'
        req = self._gen_rpc_req("getaccountstate", params=[addr_str])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertTrue('error' in res)
        self.assertEqual(-2146233033, res['error']['code'])
        self.assertEqual('One of the identified items was in an invalid format.', res['error']['message'])

    def test_get_asset_state(self):
        asset_str = '602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7'
        req = self._gen_rpc_req("getassetstate", params=[asset_str])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result']['assetId'], '0x%s' % asset_str)
        self.assertEqual(res['result']['admin'], 'AWKECj9RD8rS8RPcpCgYVjk1DeYyHwxZm3')
        self.assertEqual(res['result']['available'], 3825482025899)

    def test_bad_asset_state(self):
        asset_str = '602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282dee'
        req = self._gen_rpc_req("getassetstate", params=[asset_str])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))

        self.assertTrue('error' in res)
        self.assertEqual(res['error']['message'], 'Unknown asset')

    def test_get_bestblockhash(self):
        req = self._gen_rpc_req("getbestblockhash", params=[])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result'], '0x370007195c10a05e355b606f8f8867239f026a925f2ddc46940f62c9136d3ff5')

    def test_get_connectioncount(self):
        # @TODO
        # Not sure if there's a great way to test this as it will always return 0 in tests
        req = self._gen_rpc_req("getconnectioncount", params=[])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result'], 0)

    def test_get_block_int(self):
        req = self._gen_rpc_req("getblock", params=[10, 1])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result']['index'], 10)
        self.assertEqual(res['result']['hash'], '0x9410bd44beb7d6febc9278b028158af2781fcfb40cf2c6067b3525d24eff19f6')
        self.assertEqual(res['result']['confirmations'], 756610)
        self.assertEqual(res['result']['nextblockhash'], '0xa0d34f68cb7a04d625ae095fa509479ec7dcb4dc87ecd865ab059d0f8a42decf')

    def test_get_block_hash(self):
        req = self._gen_rpc_req("getblock", params=['a0d34f68cb7a04d625ae095fa509479ec7dcb4dc87ecd865ab059d0f8a42decf', 1])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))

        self.assertEqual(res['result']['index'], 11)
        self.assertEqual(res['result']['confirmations'], 756609)
        self.assertEqual(res['result']['previousblockhash'], '0x9410bd44beb7d6febc9278b028158af2781fcfb40cf2c6067b3525d24eff19f6')

    def test_get_block_hash_failure(self):
        req = self._gen_rpc_req("getblock", params=['aad34f68cb7a04d625ae095fa509479ec7dcb4dc87ecd865ab059d0f8a42decf', 1])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertTrue('error' in res)
        self.assertEqual(res['error']['message'], 'Unknown block')

    def test_get_block_sysfee(self):
        req = self._gen_rpc_req("getblocksysfee", params=[13321])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result'], 230)

        # TODO: test for error when requesting invalid block height

    def test_block_non_verbose(self):
        req = self._gen_rpc_req("getblock", params=[2003, 0])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertIsNotNone(res['result'])

        output = binascii.unhexlify( res['result'])
        block = Helper.AsSerializableWithType(output, 'neo.Core.Block.Block')
        self.assertEqual(block.Index, 2003)
        self.assertEqual(len(block.Transactions), 2)

    # def test_get_contract_state(self):
    #     contract_hash = UInt160(data=bytearray(b'\x11\xc4\xd1\xf4\xfb\xa6\x19\xf2b\x88p\xd3n:\x97s\xe8tp['))
    #     req = self._gen_rpc_req("getcontractstate", params=[13321])
    #     mock_req = mock_request(json.dumps(req).encode("utf-8"))
    #     res = json.loads(self.app.home(mock_req))
    #     self.assertEqual(res['result'], 230)

    def test_get_raw_mempool(self):
        # TODO: currently returns empty list. test with list would be great
        req = self._gen_rpc_req("getrawmempool", params=[])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        mempool = res['result']

        # when running only these tests, mempool is empty. when running all tests, there are a
        # number of entries
        if len(mempool) > 0:
            for entry in mempool:
                self.assertEqual(entry[0:2], "0x")
                self.assertEqual(len(entry), 66)

    def test_get_version(self):
        # TODO: what's the nonce? on testnet live server response it's always 771199013
        req = self._gen_rpc_req("getversion", params=[])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["result"]["port"], 20332)
        self.assertEqual(res["result"]["useragent"], "/NEO-PYTHON:%s/" % __version__)
