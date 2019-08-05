"""
Run only these tests:

    $ python -m unittest neo.api.JSONRPC.test_json_rpc_api
"""
import binascii
import json
import os
import shutil
from tempfile import mkdtemp
from unittest import SkipTest, skip

from aiohttp.test_utils import AioHTTPTestCase
from mock import patch

from neo import __version__
from neo.Blockchain import GetBlockchain
from neo.IO.Helper import Helper
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Network.node import NeoNode
from neo.Settings import ROOT_INSTALL_PATH, settings
from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Wallets.utils import to_aes_key
from neo.api.JSONRPC.JsonRpcApi import JsonRpcApi
from neo.Network.nodemanager import NodeManager


class JsonRpcApiTestCase(BlockchainFixtureTestCase, AioHTTPTestCase):

    def __init__(self, *args, **kwargs):
        super(JsonRpcApiTestCase, self).__init__(*args, **kwargs)
        self.api_server = JsonRpcApi()

    @classmethod
    def leveldb_testpath(cls):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    async def get_application(self):
        """
        Override the get_app method to return your application.
        """

        return self.api_server.app

    def do_test_get(self, url, data=None):
        async def test_get_route(url, data=None):
            resp = await self.client.get(url, data=data)
            text = await resp.text()
            return text

        return self.loop.run_until_complete(test_get_route(url, data))

    def do_test_post(self, url, data=None, json=None):
        if data is not None and json is not None:
            raise ValueError("cannot specify `data` and `json` at the same time")

        async def test_get_route(url, data=None, json=None):
            if data:
                resp = await self.client.post(url, data=data)
            else:
                resp = await self.client.post(url, json=json)

            text = await resp.text()
            return text

        return self.loop.run_until_complete(test_get_route(url, data, json))

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
        ret = "/?jsonrpc=2.0&id=%s&method=%s&params=[]" % (request, method)
        if params:
            ret = "/?jsonrpc=2.0&id=%s&method=%s&params=%s" % (request, method, params)
        return ret

    @SkipTest
    def test_HTTP_OPTIONS_request(self):
        # see constructor of JsonRPC api why we're skipping. CORS related
        async def test_get_route():
            resp = await self.client.options("/")
            text = await resp.text()
            return json.loads(text)

        res = self.loop.run_until_complete(test_get_route())

        self.assertTrue("GET" in res['supported HTTP methods'])
        self.assertTrue("POST" in res['supported HTTP methods'])
        self.assertTrue("default" in res['JSON-RPC server type'])

    @SkipTest
    def test_invalid_request_method(self):
        # test HEAD method
        async def test_get_route():
            resp = await self.client.head("/?test")
            text = await resp.text()
            return json.loads(text)

        res = self.loop.run_until_complete(test_get_route())

        self.assertEqual(res["error"]["code"], -32600)
        self.assertEqual(res["error"]["message"], 'HEAD is not a supported HTTP method')

    def test_invalid_json_payload(self):
        # test POST requests
        res = json.loads(self.do_test_post("/", b"{ invalid"))
        self.assertEqual(res["error"]["code"], -32700)

        res = json.loads(self.do_test_post("/", json.dumps({"some": "stuff"}).encode("utf-8")))
        self.assertEqual(res["error"]["code"], -32600)

        # test GET requests
        res = json.loads(self.do_test_get("/"))
        self.assertEqual(res["error"]["code"], -32600)

        res = json.loads(self.do_test_get("/?%20invalid"))  # equivalent to "/? invalid"
        self.assertEqual(res["error"]["code"], -32600)

        res = json.loads(self.do_test_get("/?some=stuff"))
        self.assertEqual(res["error"]["code"], -32600)

    def test_initial_setup(self):
        self.assertTrue(GetBlockchain().GetBlock(0).Hash.To0xString(), '0x996e37358dc369912041f966f8c5d8d3a8255ba5dcbd3447f8a82b55db869099')

    def test_missing_fields(self):
        # test POST requests
        req = self._gen_post_rpc_req("foo")
        del req["jsonrpc"]
        res = json.loads(self.do_test_post("/", data=req))
        self.assertEqual(res["error"]["code"], -32700)
        self.assertEqual(res["error"]["message"], "Parse error")

        req = self._gen_post_rpc_req("foo")
        del req["id"]
        res = json.loads(self.do_test_post("/", data=req))
        self.assertEqual(res["error"]["code"], -32700)
        self.assertEqual(res["error"]["message"], "Parse error")

        req = self._gen_post_rpc_req("foo")
        del req["method"]
        res = json.loads(self.do_test_post("/", data=req))
        self.assertEqual(res["error"]["code"], -32700)
        self.assertEqual(res["error"]["message"], "Parse error")

        # test GET requests
        url = "/?method=foo&id=2"
        res = json.loads(self.do_test_get(url, data=req))
        self.assertEqual(res["error"]["code"], -32600)
        self.assertEqual(res["error"]["message"], "Invalid value for 'jsonrpc'")

        url = "/?jsonrpc=2.0&method=foo"
        res = json.loads(self.do_test_get(url, data=req))
        self.assertEqual(res["error"]["code"], -32600)
        self.assertEqual(res["error"]["message"], "Field 'id' is missing")

        url = "/?jsonrpc=2.0&id=2"
        res = json.loads(self.do_test_get(url, data=req))
        self.assertEqual(res["error"]["code"], -32600)
        self.assertEqual(res["error"]["message"], "Field 'method' is missing")

    def test_invalid_method(self):
        # test POST requests
        req = self._gen_post_rpc_req("invalid", request_id="42")
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res["id"], "42")
        self.assertEqual(res["error"]["code"], -32601)
        self.assertEqual(res["error"]["message"], "Method not found")

        # test GET requests
        url = self._gen_get_rpc_req("invalid")
        res = json.loads(self.do_test_get(url))
        self.assertEqual(res["error"]["code"], -32601)
        self.assertEqual(res["error"]["message"], "Method not found")

    def test_getblockcount(self):
        # test POST requests
        req = self._gen_post_rpc_req("getblockcount")
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(GetBlockchain().Height + 1, res["result"])

        # test GET requests ...next we will test a complex method; see test_sendmany_complex
        url = self._gen_get_rpc_req("getblockcount")
        res = json.loads(self.do_test_get(url))
        self.assertEqual(GetBlockchain().Height + 1, res["result"])

    def test_getblockhash(self):
        req = self._gen_post_rpc_req("getblockhash", params=[2])
        res = json.loads(self.do_test_post("/", json=req))

        # taken from neoscan
        expected_blockhash = '0x049db9f55ac45201c128d1a40d0ef9d4bdc58db97d47d985ce8d66511a1ef9eb'
        self.assertEqual(expected_blockhash, res["result"])

    def test_getblockhash_failure(self):
        req = self._gen_post_rpc_req("getblockhash", params=[-1])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(-100, res["error"]["code"])
        self.assertEqual("Invalid Height", res["error"]["message"])

    def test_account_state(self):
        addr_str = 'AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y'
        req = self._gen_post_rpc_req("getaccountstate", params=[addr_str])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result']['balances'][0]['value'], '99989900')
        self.assertEqual(res['result']['balances'][0]['asset'], '0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b'),
        self.assertEqual(res['result']['address'], addr_str)

    def test_account_state_not_existing_yet(self):
        addr_str = 'AHozf8x8GmyLnNv8ikQcPKgRHQTbFi46u2'
        req = self._gen_post_rpc_req("getaccountstate", params=[addr_str])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result']['balances'], [])
        self.assertEqual(res['result']['address'], addr_str)

    def test_account_state_failure(self):
        addr_str = 'AK2nJJpJr6o664CWJKi1QRXjqeic2zRp81'
        req = self._gen_post_rpc_req("getaccountstate", params=[addr_str])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertTrue('error' in res)
        self.assertEqual(-2146233033, res['error']['code'])
        self.assertEqual('One of the identified items was in an invalid format.', res['error']['message'])

    def test_get_asset_state_hash(self):
        asset_str = '602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7'
        req = self._gen_post_rpc_req("getassetstate", params=[asset_str])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result']['assetId'], '0x%s' % asset_str)
        self.assertEqual(res['result']['admin'], 'AWKECj9RD8rS8RPcpCgYVjk1DeYyHwxZm3')
        self.assertEqual(res['result']['available'], 0)

    def test_get_asset_state_neo(self):
        asset_str = 'neo'
        req = self._gen_post_rpc_req("getassetstate", params=[asset_str])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result']['assetId'], '0x%s' % str(GetBlockchain().SystemShare().Hash))
        self.assertEqual(res['result']['admin'], 'Abf2qMs1pzQb8kYk9RuxtUb9jtRKJVuBJt')
        self.assertEqual(res['result']['available'], 10000000000000000)

    def test_get_asset_state_gas(self):
        asset_str = 'GAS'
        req = self._gen_post_rpc_req("getassetstate", params=[asset_str])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result']['assetId'], '0x%s' % str(GetBlockchain().SystemCoin().Hash))
        self.assertEqual(res['result']['amount'], 10000000000000000)
        self.assertEqual(res['result']['admin'], 'AWKECj9RD8rS8RPcpCgYVjk1DeYyHwxZm3')

    def test_get_asset_state_0x(self):
        asset_str = '0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7'
        req = self._gen_post_rpc_req("getassetstate", params=[asset_str])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result']['assetId'], asset_str)

    def test_bad_asset_state(self):
        asset_str = '602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282dee'
        req = self._gen_post_rpc_req("getassetstate", params=[asset_str])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertTrue('error' in res)
        self.assertEqual(res['error']['message'], 'Unknown asset')

    def test_get_bestblockhash(self):
        req = self._gen_post_rpc_req("getbestblockhash", params=[])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result'], '0x0c9f39eddd425aba7c27543a90768093a90c76a35090ef9b413027927e887811')

    def test_get_connectioncount(self):
        # make sure we have a predictable state
        nodemgr = self.api_server.nodemgr
        nodemgr.reset_for_test()
        nodemgr.nodes = [object(), object()]

        req = self._gen_post_rpc_req("getconnectioncount", params=[])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result'], 2)
        nodemgr.reset_for_test()

    def test_get_block_int(self):
        req = self._gen_post_rpc_req("getblock", params=[10, 1])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result']['index'], 10)
        self.assertEqual(res['result']['hash'], '0xd69e7a1f62225a35fed91ca578f33447d93fa0fd2b2f662b957e19c38c1dab1e')
        self.assertEqual(res['result']['confirmations'], GetBlockchain().Height - 10 + 1)
        self.assertEqual(res['result']['nextblockhash'], '0x2b1c78633dae7ab81f64362e0828153079a17b018d779d0406491f84c27b086f')

    def test_get_block_hash(self):
        req = self._gen_post_rpc_req("getblock", params=['2b1c78633dae7ab81f64362e0828153079a17b018d779d0406491f84c27b086f', 1])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result']['index'], 11)
        self.assertEqual(res['result']['confirmations'], GetBlockchain().Height - 11 + 1)
        self.assertEqual(res['result']['previousblockhash'], '0xd69e7a1f62225a35fed91ca578f33447d93fa0fd2b2f662b957e19c38c1dab1e')

    def test_get_block_hash_0x(self):
        req = self._gen_post_rpc_req("getblock", params=['0x2b1c78633dae7ab81f64362e0828153079a17b018d779d0406491f84c27b086f', 1])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result']['index'], 11)

    def test_get_block_hash_failure(self):
        req = self._gen_post_rpc_req("getblock", params=['aad34f68cb7a04d625ae095fa509479ec7dcb4dc87ecd865ab059d0f8a42decf', 1])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertTrue('error' in res)
        self.assertEqual(res['error']['message'], 'Unknown block')

    def test_get_block_sysfee(self):
        req = self._gen_post_rpc_req("getblocksysfee", params=[9479])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result'], 1560)

        # test negative block
        req = self._gen_post_rpc_req("getblocksysfee", params=[-1])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertTrue('error' in res)
        self.assertEqual(res['error']['message'], 'Invalid Height')

        # test block exceeding max block height
        req = self._gen_post_rpc_req("getblocksysfee", params=[3000000000])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertTrue('error' in res)
        self.assertEqual(res['error']['message'], 'Invalid Height')

    def test_block_non_verbose(self):
        req = self._gen_post_rpc_req("getblock", params=[2003, 0])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertIsNotNone(res['result'])

        # we should be able to instantiate a matching block with the result
        output = binascii.unhexlify(res['result'])
        block = Helper.AsSerializableWithType(output, 'neo.Core.Block.Block')
        self.assertEqual(block.Index, 2003)
        self.assertEqual(len(block.Transactions), 1)

    def test_get_contract_state(self):
        contract_hash = "b9fbcff6e50fd381160b822207231233dd3c56c2"
        req = self._gen_post_rpc_req("getcontractstate", params=[contract_hash])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result']['code_version'], '')
        self.assertEqual(res['result']['properties']['storage'], True)
        self.assertEqual(res['result']['hash'], '0xb9fbcff6e50fd381160b822207231233dd3c56c2')
        self.assertEqual(res['result']['returntype'], "ByteArray")
        self.assertEqual(res['result']['parameters'], ["String", "Array"])

    def test_get_contract_state_0x(self):
        contract_hash = "0xb9fbcff6e50fd381160b822207231233dd3c56c2"
        req = self._gen_post_rpc_req("getcontractstate", params=[contract_hash])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result']['code_version'], '')

    def test_get_contract_state_not_found(self):
        contract_hash = '0xb9fbcff6e50fd381160b822207231233dd3c56c1'
        req = self._gen_post_rpc_req("getcontractstate", params=[contract_hash])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertTrue('error' in res)
        self.assertEqual(res['error']['message'], 'Unknown contract')

    @skip("outdated compared to neo-cli")
    def test_get_raw_mempool(self):
        nodemgr = self.api_server.nodemgr
        nodemgr.reset_for_test()

        raw_tx = b'd100644011111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111081234567890abcdef0415cd5b0769cc4ee2f1c9f4e0782756dabf246d0a4fe60a035400000000'
        tx = Helper.AsSerializableWithType(binascii.unhexlify(raw_tx), 'neo.Core.TX.InvocationTransaction.InvocationTransaction')
        nodemgr.mempool.add_transaction(tx)

        req = self._gen_post_rpc_req("getrawmempool", params=[])
        res = json.loads(self.do_test_post("/", json=req))

        mempool = res['result']

        self.assertEqual(1, len(mempool))
        self.assertEqual(tx.Hash.To0xString(), mempool[0])
        nodemgr.reset_for_test()

    def test_get_version(self):
        nodemgr = NodeManager()
        req = self._gen_post_rpc_req("getversion", params=[])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res["result"]["port"], 20332)
        self.assertEqual(res["result"]["nonce"], nodemgr.id)
        self.assertEqual(res["result"]["useragent"], "/NEO-PYTHON:%s/" % __version__)

    def test_validate_address(self):
        # example from docs.neo.org
        req = self._gen_post_rpc_req("validateaddress", params=["AQVh2pG732YvtNaxEGkQUei3YA4cvo7d2i"])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertTrue(res["result"]["isvalid"])

        # example from docs.neo.org
        req = self._gen_post_rpc_req("validateaddress", params=["152f1muMCNa7goXYhYAQC61hxEgGacmncB"])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertFalse(res["result"]["isvalid"])

        # catch completely invalid argument
        req = self._gen_post_rpc_req("validateaddress", params=[])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertTrue('error' in res)
        self.assertEqual('Missing argument', res['error']['message'])

        # catch completely invalid argument
        req = self._gen_post_rpc_req("validateaddress", params=[""])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertTrue('error' in res)
        self.assertEqual('Missing argument', res['error']['message'])

    def test_getrawtx_1(self):
        txid = 'f999c36145a41306c846ea80290416143e8e856559818065be3f4e143c60e43a'
        req = self._gen_post_rpc_req("getrawtransaction", params=[txid, 1])
        res = json.loads(self.do_test_post("/", json=req))['result']
        self.assertEqual(res['blockhash'], '0x6088bf9d3b55c67184f60b00d2e380228f713b4028b24c1719796dcd2006e417')
        self.assertEqual(res['txid'], "0x%s" % txid)
        self.assertEqual(res['blocktime'], 1533756500)
        self.assertEqual(res['type'], 'ContractTransaction')

    def test_getrawtx_2(self):
        txid = 'f999c36145a41306c846ea80290416143e8e856559818065be3f4e143c60e43a'
        req = self._gen_post_rpc_req("getrawtransaction", params=[txid, 0])
        res = json.loads(self.do_test_post("/", json=req))['result']
        expected = '8000012023ba2703c53263e8d6e522dc32203339dcd8eee901ff6a846c115ef1fb88664b00aa67f2c95e9405286db1b56c9120c27c698490530000029b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc50010a5d4e8000000affb37f5fdb9c6fec48d9f0eee85af82950f9b4a9b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500f01b9b0986230023ba2703c53263e8d6e522dc32203339dcd8eee9014140a88bd1fcfba334b06da0ce1a679f80711895dade50352074e79e438e142dc95528d04a00c579398cb96c7301428669a09286ae790459e05e907c61ab8a1191c62321031a6c6fbbdf02ca351745fa86b9ba5a9452d785ac4f7fc2b7548ca2a46c4fcf4aac'
        self.assertEqual(res, expected)

    def test_getrawtx_3(self):
        txid = 'f999c36145a41306c846ea80290416143e8e856559818065be3f4e143c60e43b'
        req = self._gen_post_rpc_req("getrawtransaction", params=[txid, 0])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertTrue('error' in res)
        self.assertEqual(res['error']['message'], 'Unknown Transaction')

    def test_get_storage_item(self):
        contract_hash = 'b9fbcff6e50fd381160b822207231233dd3c56c2'
        storage_key = binascii.hexlify(b'in_circulation').decode('utf-8')
        req = self._gen_post_rpc_req("getstorage", params=[contract_hash, storage_key])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result'], '00a031a95fe300')
        actual_val = int.from_bytes(binascii.unhexlify(res['result'].encode('utf-8')), 'little')
        self.assertEqual(actual_val, 250000000000000)

    def test_get_storage_item2(self):
        contract_hash = '90ea0b9b8716cf0ceca5b24f6256adf204f444d9'
        storage_key = binascii.hexlify(b'in_circulation').decode('utf-8')
        req = self._gen_post_rpc_req("getstorage", params=[contract_hash, storage_key])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result'], '00c06e31d91001')

    def test_get_storage_item_key_not_found(self):
        contract_hash = 'b9fbcff6e50fd381160b822207231233dd3c56c1'
        storage_key = binascii.hexlify(b'blah').decode('utf-8')
        req = self._gen_post_rpc_req("getstorage", params=[contract_hash, storage_key])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result'], None)

    def test_get_storage_item_contract_not_found(self):
        contract_hash = 'b9fbcff6e50fd381160b822207231233dd3c56c1'
        storage_key = binascii.hexlify(b'blah').decode('utf-8')
        req = self._gen_post_rpc_req("getstorage", params=[contract_hash, storage_key])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result'], None)

    def test_get_storage_item_bad_contract_hash(self):
        contract_hash = 'b9fbcff6e50f01160b822207231233dd3c56c1'
        storage_key = binascii.hexlify(b'blah').decode('utf-8')
        req = self._gen_post_rpc_req("getstorage", params=[contract_hash, storage_key])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertTrue('error' in res)
        self.assertIn('Invalid UInt', res['error']['message'])

    def test_gettxout(self):
        txid = 'a2a37fd2ab7048d70d51eaa8af2815e0e542400329b05a34274771174180a7e8'
        output_index = 0
        req = self._gen_post_rpc_req("gettxout", params=[txid, output_index])
        res = json.loads(self.do_test_post("/", json=req))
        # will return `null` if not found
        self.assertEqual(None, res["result"])

        # output with index 1 is unspent, so should return valid values
        # The txid need to be updated whenever we spend NEO from the address: AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y (coz wallet)
        txid = '42978cd563e9e95550fb51281d9071e27ec94bd42116836f0d0141d57a346b3e'
        output_index = 1
        req = self._gen_post_rpc_req("gettxout", params=[txid, output_index])
        res = json.loads(self.do_test_post("/", json=req))

        expected_asset = '0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b'
        expected_value = "99989900"
        expected_address = 'AK2nJJpJr6o664CWJKi1QRXjqeic2zRp8y'

        self.assertEqual(output_index, res["result"]["n"])
        self.assertEqual(expected_address, res["result"]["address"])
        self.assertEqual(expected_asset, res["result"]["asset"])
        self.assertEqual(expected_value, res["result"]["value"])

        # now test a different index
        txid = 'f999c36145a41306c846ea80290416143e8e856559818065be3f4e143c60e43a'
        output_index = 0
        req = self._gen_post_rpc_req("gettxout", params=[txid, output_index])
        res = json.loads(self.do_test_post("/", json=req))

        expected_value = "10000"
        self.assertEqual(output_index, res["result"]["n"])
        self.assertEqual(expected_value, res["result"]["value"])

    def test_send_raw_tx(self):

        with patch('neo.Network.node.NeoNode.relay', return_value=self.async_return(True)):
            nodemgr = self.api_server.nodemgr
            nodemgr.reset_for_test()
            nodemgr.nodes = [NeoNode(object(), object())]

            raw_tx = '8000000001e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c6000ca9a3b0000000048033b58ef547cbf54c8ee2f72a42d5b603c00af'
            req = self._gen_post_rpc_req("sendrawtransaction", params=[raw_tx])
            res = json.loads(self.do_test_post("/", json=req))
            self.assertEqual(res['result'], True)
            nodemgr.reset_for_test()

    def test_send_raw_tx_bad(self):
        with patch('neo.Network.node.NeoNode.relay', return_value=self.async_return(True)):
            nodemgr = self.api_server.nodemgr
            nodemgr.reset_for_test()
            nodemgr.nodes = [NeoNode(object(), object())]

            raw_tx = '80000001b10ad9ec660bf343c0eb411f9e05b4fa4ad8abed31d4e4dc5bb6ae416af0c4de000002e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c60c8db571300000000af12a8687b14948bc4a008128a550a63695bc1a5e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c603808b44002000000eca8fcf94e7a2a7fc3fd54ae0ed3d34d52ec25900141404749ce868ed9588f604eeeb5c523db39fd57cd7f61d04393a1754c2d32f131d67e6b1ec561ac05012b7298eb5ff254487c76de0b2a0c4d097d17cec708c0a9802321025b5c8cdcb32f8e278e111a0bf58ebb463988024bb4e250aa4310b40252030b60ac'
            req = self._gen_post_rpc_req("sendrawtransaction", params=[raw_tx])
            res = json.loads(self.do_test_post("/", json=req))
            self.assertEqual(res['result'], False)
            nodemgr.reset_for_test()

    def test_send_raw_tx_bad_2(self):
        with patch('neo.Network.node.NeoNode.relay', return_value=self.async_return(True)):
            nodemgr = self.api_server.nodemgr
            nodemgr.reset_for_test()
            nodemgr.nodes = [NeoNode(object(), object())]

            raw_tx = '80000001b10ad9ec660bf343c0eb411f9e05b4fa4ad8abed31d4e4dc5bb6ae416af0c4de000002e72d286979ee6cbb7e65dfddfb2e384100b8d148e7758de42e4168b71792c60c8db571300000000af12a8687b14948bc4a008128a550a63695bc1a5e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c603808b44002000000eca8fcf94e7a2a7fc3fd54ae0ed3d34d52ec25900141404749ce868ed9588f604eeeb5c523db39fd57cd7f61d04393a1754c2d32f131d67e6b1ec561ac05012b7298eb5ff254487c76de0b2a0c4d097d17cec708c0a9802321025b5c8cdcb32f8e278e111a0bf58ebb463988024bb4e250aa4310b40252030b60ac'
            req = self._gen_post_rpc_req("sendrawtransaction", params=[raw_tx])
            res = json.loads(self.do_test_post("/", json=req))
            self.assertTrue('error' in res)
            self.assertEqual(res['error']['code'], -32603)
            nodemgr.reset_for_test()

    @SkipTest
    def test_gzip_compression(self):
        # TODO: figure out how to properly validate gzip with aiohttp
        #  note it is applied using the @json decorator in neo/api/utils.py
        req = self._gen_post_rpc_req("getblock", params=['0x2b1c78633dae7ab81f64362e0828153079a17b018d779d0406491f84c27b086f', 1])
        body = json.dumps(req).encode("utf-8")

        async def test_get_route(url, data=None, headers=None):
            resp = await self.client.post(url, json=data, headers=headers)
            return resp

        # first validate that we get a gzip response if we accept gzip encoding
        resp = self.loop.run_until_complete(test_get_route("/", headers={'Accept-Encoding': "deflate, gzip;q=1.0, *;q=0.5"}))
        self.assertEqual(83, resp.content_length)

        resp = self.loop.run_until_complete(test_get_route("/", headers={'Accept-Encoding': ""}))
        self.assertEqual(2283, resp.content_length)

    def test_getpeers(self):
        # Given this is an isolated environment and there are no peers
        # let's simulate that at least some addresses are known
        nodemgr = self.api_server.nodemgr
        nodemgr.reset_for_test()
        node1 = NeoNode(object, object)
        node1.address = "127.0.0.1:2222"
        nodemgr.nodes.append(node1)

        nodemgr.known_addresses = ["127.0.0.1:20333", "127.0.0.2:20334"]
        nodemgr.bad_addresses = ["127.0.0.1:20335"]

        req = self._gen_post_rpc_req("getpeers", params=[])
        res = json.loads(self.do_test_post("/", json=req))

        self.assertEqual(1, len(res['result']['connected']))
        self.assertEqual(2, len(res['result']['unconnected']))
        self.assertEqual(1, len(res['result']['bad']))

    def test_getwalletheight_no_wallet(self):
        req = self._gen_post_rpc_req("getwalletheight", params=["some id here"])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})

        self.assertEqual(error.get('code', None), -400)
        self.assertEqual(error.get('message', None), "Access denied.")

    def test_getwalletheight(self):
        self.api_server.wallet = UserWallet.Open(os.path.join(ROOT_INSTALL_PATH, "neo/data/neo-privnet.sample.wallet"), to_aes_key("coz"))

        req = self._gen_post_rpc_req("getwalletheight", params=[])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(1, res.get('result'))

    def test_getbalance_no_wallet(self):
        req = self._gen_post_rpc_req("getbalance", params=["some id here"])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})

        self.assertEqual(error.get('code', None), -400)
        self.assertEqual(error.get('message', None), "Access denied.")

    def test_getbalance_neo_with_wallet(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )

        neo_id = "c56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b"
        req = self._gen_post_rpc_req("getbalance", params=[neo_id])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertIn('Balance', res.get('result').keys())
        self.assertEqual(res['result']['Balance'], "150")
        self.assertIn('Confirmed', res.get('result').keys())
        self.assertEqual(res['result']['Confirmed'], "50.0")

        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(test_wallet_path)

    def test_getbalance_token_with_wallet(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_2_path(),
            WalletFixtureTestCase.wallet_2_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_2_pass())
        )

        fake_token_id = "NXT4"
        req = self._gen_post_rpc_req("getbalance", params=[fake_token_id])
        res = json.loads(self.do_test_post("/", json=req))

        self.assertIn('Balance', res.get('result').keys())
        self.assertEqual(res['result']['Balance'], "1000")
        self.assertNotIn('Confirmed', res.get('result').keys())

        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(test_wallet_path)

    def test_listaddress_no_wallet(self):
        req = self._gen_post_rpc_req("listaddress", params=[])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})

        self.assertEqual(error.get('code', None), -400)
        self.assertEqual(error.get('message', None), "Access denied.")

    def test_listaddress_with_wallet(self):
        test_wallet_path = os.path.join(mkdtemp(), "listaddress.db3")
        self.api_server.wallet = UserWallet.Create(
            test_wallet_path,
            to_aes_key('awesomepassword')
        )

        req = self._gen_post_rpc_req("listaddress", params=[])
        res = json.loads(self.do_test_post("/", json=req))
        results = res.get('result', [])
        self.assertGreater(len(results), 0)
        self.assertIn(results[0].get('address', None),
                      self.api_server.wallet.Addresses)
        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(test_wallet_path)

    def test_getnewaddress_no_wallet(self):
        req = self._gen_post_rpc_req("getnewaddress", params=[])
        res = json.loads(self.do_test_post("/", json=req))

        error = res.get('error', {})

        self.assertEqual(error.get('code', None), -400)
        self.assertEqual(error.get('message', None), "Access denied.")

    def test_getnewaddress_with_wallet(self):
        test_wallet_path = os.path.join(mkdtemp(), "getnewaddress.db3")
        self.api_server.wallet = UserWallet.Create(
            test_wallet_path,
            to_aes_key('awesomepassword')
        )

        old_addrs = self.api_server.wallet.Addresses

        req = self._gen_post_rpc_req("getnewaddress", params=[])
        res = json.loads(self.do_test_post("/", json=req))
        result = res.get('result')

        self.assertNotIn(result, old_addrs)
        self.assertIn(result, self.api_server.wallet.Addresses)

        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(test_wallet_path)

    def test_valid_multirequest(self):
        # test POST requests ...should pass
        raw_block_request = {"jsonrpc": "2.0", "method": "getblock", "params": [1], "id": 1}
        verbose_block_request = {"jsonrpc": "2.0", "method": "getblock", "params": [1, 1], "id": 2}

        multi_request = json.dumps([raw_block_request, verbose_block_request])
        res = json.loads(self.do_test_post("/", data=multi_request))

        self.assertEqual(type(res), list)
        self.assertEqual(len(res), 2)
        expected_raw_block = '00000000999086db552ba8f84734bddca55b25a8d3d8c5f866f941209169c38d35376e9902c78a8ae8efe7e9d46f76399a9d9449155e861d6849c110ea5f6b7d146a9a8aa4d1305b01000000bd7d9349807816a1be48d3a3f5d10013ab9ffee489706078714f1ea201c340dcbeadb300ff983f40f537ba6d63721cafda183b2cd161801ffb0f8316f100b63dbfbae665bba75fa1a954f14351f91cbf07bf90e60ff79f3e9076bcb1b5121840665a065b967ac0bddddd1ed1b9a7c02c7c434e804e6e77d019778b74d6642423401e35dd9d8195d6896322e7ed6922c1eb8b086391b884a6acda2c34b70927f84075c25a44184ce92f7d7af1d2f22bee69374dd1bf0327f8956ede0dc23dda90106cf555fb8202fe6db9acda1d0b4fff8fdcd0404daa4b359c73017c7cdb8009468b532102103a7f7dd016558597f7960d27c516a4394fd968b9e65155eb4b013e4040406e2102a7bc55fe8684e0119768d104ba30795bdcc86619e864add26156723ed185cd622102b3622bf4017bdfe317c58aed5f4c753f206b7db896046fa7d774bbc4bf7f8dc22103d90c07df63e690ce77912e10ab51acc944b66860237b608c4f8f8309e71ee69954ae010000bd7d934900000000'
        self.assertEqual(res[0]['result'], expected_raw_block)
        expected_verbose_hash = '0x55f745c9098d5d5bdaff9f8f32aad29c904c83d9832b48c16e677d30c7da4273'
        self.assertEqual(res[1]['result']['hash'], expected_verbose_hash)

        # test GET requests ...should fail
        raw_request = "/?[jsonrpc=2.0&method=getblock&params=[1]&id=1,jsonrpc=2.0&method=getblock&params=[1,1]&id=2]"
        res = json.loads(self.do_test_get(raw_request))

        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32600)
        self.assertEqual(error.get('message', None), "Invalid value for 'jsonrpc'")

    def test_multirequest_with_1_invalid_request(self):
        """
        We provide 2 requests, first one invalid and should return and error, second one  valid and should still come up with correct results
        """
        # block request of invalid block, should fail
        raw_block_request = {"jsonrpc": "2.0", "method": "getblock", "params": [10000000000], "id": 1}
        verbose_block_request = {"jsonrpc": "2.0", "method": "getblock", "params": [1, 1], "id": 2}

        multi_request = json.dumps([raw_block_request, verbose_block_request])
        res = json.loads(self.do_test_post("/", data=multi_request))

        self.assertEqual(type(res), list)
        self.assertEqual(len(res), 2)

        # test for errors in first invalid request
        error = res[0].get('error', {})
        self.assertEqual(error.get('code', None), -100)
        self.assertEqual(error.get('message', None), "Unknown block")

        # test for success in second valid request
        expected_verbose_hash = '0x55f745c9098d5d5bdaff9f8f32aad29c904c83d9832b48c16e677d30c7da4273'
        self.assertEqual(res[1]['result']['hash'], expected_verbose_hash)

    def test_send_to_address_no_wallet(self):
        req = self._gen_post_rpc_req("sendtoaddress", params=[])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})

        self.assertEqual(error.get('code', None), -400)
        self.assertEqual(error.get('message', None), "Access denied.")

    def test_send_to_address_wrong_arguments(self):
        test_wallet_path = os.path.join(mkdtemp(), "sendtoaddress.db3")
        self.api_server.wallet = UserWallet.Create(
            test_wallet_path,
            to_aes_key('awesomepassword')
        )

        req = self._gen_post_rpc_req("sendtoaddress", params=["arg"])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})

        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")

        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(test_wallet_path)

    def test_send_to_address_simple(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'

        with patch('neo.Network.nodemanager.NodeManager.relay', return_value=self.async_return(True)):
            req = self._gen_post_rpc_req("sendtoaddress", params=['gas', address, 1])
            res = json.loads(self.do_test_post("/", json=req))

        self.assertEqual(res.get('jsonrpc', None), '2.0')
        self.assertIn('txid', res.get('result', {}).keys())
        self.assertIn('vin', res.get('result', {}).keys())

        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_send_to_address_with_fee(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'

        with patch('neo.Network.nodemanager.NodeManager.relay', return_value=self.async_return(True)):
            req = self._gen_post_rpc_req("sendtoaddress", params=['neo', address, 1, 0.005])
            res = json.loads(self.do_test_post("/", json=req))

        self.assertEqual(res.get('jsonrpc', None), '2.0')
        self.assertIn('txid', res.get('result', {}).keys())
        self.assertEqual(res['result']['net_fee'], "0.005")

        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_send_to_address_bad_assetid(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'

        req = self._gen_post_rpc_req("sendtoaddress", params=['ga', address, 1])
        res = json.loads(self.do_test_post("/", json=req))

        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")

        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_send_to_address_bad_address(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaX'  # "AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaX" is too short causing ToScriptHash to fail

        req = self._gen_post_rpc_req("sendtoaddress", params=['gas', address, 1])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")

        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_send_to_address_negative_amount(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'

        req = self._gen_post_rpc_req("sendtoaddress", params=['gas', address, -1])
        res = json.loads(self.do_test_post("/", json=req))

        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")

        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_send_to_address_zero_amount(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'

        req = self._gen_post_rpc_req("sendtoaddress", params=['gas', address, 0])
        res = json.loads(self.do_test_post("/", json=req))

        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")

        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_send_to_address_negative_fee(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'

        req = self._gen_post_rpc_req("sendtoaddress", params=['gas', address, 1, -0.005])
        res = json.loads(self.do_test_post("/", json=req))

        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")

        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_send_to_address_insufficient_funds(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'

        req = self._gen_post_rpc_req("sendtoaddress", params=['gas', address, 51])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -300)
        self.assertEqual(error.get('message', None), "Insufficient funds")

        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_send_to_address_fails_to_sign_tx(self):
        with patch('neo.Implementations.Wallets.peewee.UserWallet.UserWallet.Sign', return_value='False'):
            test_wallet_path = shutil.copyfile(
                WalletFixtureTestCase.wallet_1_path(),
                WalletFixtureTestCase.wallet_1_dest()
            )
            self.api_server.wallet = UserWallet.Open(
                test_wallet_path,
                to_aes_key(WalletFixtureTestCase.wallet_1_pass())
            )
            address = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'

            req = self._gen_post_rpc_req("sendtoaddress", params=['gas', address, 1])
            res = json.loads(self.do_test_post("/", json=req))
            self.assertEqual(res.get('jsonrpc', None), '2.0')
            self.assertIn('type', res.get('result', {}).keys())
            self.assertIn('hex', res.get('result', {}).keys())

            self.api_server.wallet.Close()
            self.api_server.wallet = None
            os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_send_from_no_wallet(self):
        req = self._gen_post_rpc_req("sendfrom", params=[])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -400)
        self.assertEqual(error.get('message', None), "Access denied.")

    def test_send_from_wrong_arguments(self):
        test_wallet_path = os.path.join(mkdtemp(), "sendfromaddress.db3")
        self.api_server.wallet = UserWallet.Create(
            test_wallet_path,
            to_aes_key('awesomepassword')
        )
        req = self._gen_post_rpc_req("sendfrom", params=["arg"])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")
        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(test_wallet_path)

    def test_send_from_simple(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address_to = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
        address_from = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'

        with patch('neo.Network.nodemanager.NodeManager.relay', return_value=self.async_return(True)):
            req = self._gen_post_rpc_req("sendfrom", params=['neo', address_from, address_to, 1])
            res = json.loads(self.do_test_post("/", json=req))

        self.assertEqual(res.get('jsonrpc', None), '2.0')
        self.assertIn('txid', res.get('result', {}).keys())
        self.assertIn('vin', res.get('result', {}).keys())
        self.assertEqual(address_to, res['result']['vout'][0]['address'])
        self.assertEqual(address_from, res['result']['vout'][1]['address'])
        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_send_from_complex(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address_to = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
        address_from = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'
        amount = 1
        net_fee = 0.005
        change_addr = 'AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkEm'
        address_from_account_state = GetBlockchain().GetAccountState(address_from).ToJson()
        address_from_gas = next(filter(lambda b: b['asset'] == '0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7',
                                       address_from_account_state['balances']))
        address_from_gas_bal = address_from_gas['value']

        with patch('neo.Network.nodemanager.NodeManager.relay', return_value=self.async_return(True)):
            req = self._gen_post_rpc_req("sendfrom", params=['gas', address_from, address_to, amount, net_fee, change_addr])
            res = json.loads(self.do_test_post("/", json=req))

        self.assertEqual(res.get('jsonrpc', None), '2.0')
        self.assertIn('txid', res.get('result', {}).keys())
        self.assertEqual(address_to, res['result']['vout'][0]['address'])
        self.assertEqual(change_addr, res['result']['vout'][1]['address'])
        self.assertEqual(float(address_from_gas_bal) - amount - net_fee, float(res['result']['vout'][1]['value']))
        self.assertEqual(res['result']['net_fee'], "0.005")

        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_send_from_bad_assetid(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address_to = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
        address_from = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'
        req = self._gen_post_rpc_req("sendfrom", params=['nep', address_from, address_to, 1])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")
        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_send_from_negative_amount(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address_to = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
        address_from = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'
        req = self._gen_post_rpc_req("sendfrom", params=['neo', address_from, address_to, -1])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")
        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_send_from_zero_amount(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address_to = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
        address_from = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'
        req = self._gen_post_rpc_req("sendfrom", params=['neo', address_from, address_to, 0])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")
        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_send_from_bad_from_addr(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address_to = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
        address_from = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc'  # "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc" is too short causing ToScriptHash to fail
        req = self._gen_post_rpc_req("sendfrom", params=['neo', address_from, address_to, 1])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")
        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_send_from_bad_to_addr(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address_to = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaX'  # "AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaX" is too short causing ToScriptHash to fail
        address_from = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'
        req = self._gen_post_rpc_req("sendfrom", params=['neo', address_from, address_to, 1])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")
        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_send_from_negative_fee(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address_to = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
        address_from = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'
        req = self._gen_post_rpc_req("sendfrom", params=['neo', address_from, address_to, 1, -0.005])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")
        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_send_from_bad_change_addr(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address_to = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
        address_from = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'
        req = self._gen_post_rpc_req("sendfrom", params=['neo', address_from, address_to, 1, .005, 'AGYaEi3W6ndHPUmW7T12FFfsbQ6DWymkE'])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")
        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_send_from_insufficient_funds(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address_to = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
        address_from = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'
        req = self._gen_post_rpc_req("sendfrom", params=['neo', address_from, address_to, 51])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -300)
        self.assertEqual(error.get('message', None), "Insufficient funds")
        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_send_from_fails_to_sign_tx(self):
        with patch('neo.Implementations.Wallets.peewee.UserWallet.UserWallet.Sign', return_value='False'):
            test_wallet_path = shutil.copyfile(
                WalletFixtureTestCase.wallet_1_path(),
                WalletFixtureTestCase.wallet_1_dest()
            )
            self.api_server.wallet = UserWallet.Open(
                test_wallet_path,
                to_aes_key(WalletFixtureTestCase.wallet_1_pass())
            )
            address_to = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
            address_from = 'AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3'
            req = self._gen_post_rpc_req("sendfrom", params=['neo', address_from, address_to, 1])
            res = json.loads(self.do_test_post("/", json=req))

            self.assertEqual(res.get('jsonrpc', None), '2.0')
            self.assertIn('type', res.get('result', {}).keys())
            self.assertIn('hex', res.get('result', {}).keys())

            self.api_server.wallet.Close()
            self.api_server.wallet = None
            os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_sendmany_no_wallet(self):
        req = self._gen_post_rpc_req("sendmany", params=[])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -400)
        self.assertEqual(error.get('message', None), "Access denied.")

    def test_sendmany_complex_post(self):
        # test POST requests
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address_to = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
        output = [{"asset": 'neo',
                   "value": 1,
                   "address": address_to},
                  {"asset": 'neo',
                   "value": 1,
                   "address": address_to}]
        with patch('neo.Network.nodemanager.NodeManager.relay', return_value=self.async_return(True)):
            req = self._gen_post_rpc_req("sendmany", params=[output, 1, "APRgMZHZubii29UXF9uFa6sohrsYupNAvx"])
            res = json.loads(self.do_test_post("/", json=req))

        self.assertEqual(res.get('jsonrpc', None), '2.0')
        self.assertIn('txid', res.get('result', {}).keys())
        self.assertIn('vin', res.get('result', {}).keys())
        self.assertEqual('1', res['result']['net_fee'])

        # check for 2 transfers
        transfers = 0
        for info in res['result']['vout']:
            if info['address'] == "AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK":
                transfers += 1
        self.assertEqual(2, transfers)

        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

        # test GET requests
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        with patch('neo.Network.nodemanager.NodeManager.relay', return_value=self.async_return(True)):
            req = self._gen_get_rpc_req("sendmany", params=[output, 0.005, "APRgMZHZubii29UXF9uFa6sohrsYupNAvx"])
            res = json.loads(self.do_test_get(req))

        self.assertEqual(res.get('jsonrpc', None), '2.0')
        self.assertIn('txid', res.get('result', {}).keys())
        self.assertIn('vin', res.get('result', {}).keys())
        self.assertEqual('0.005', res['result']['net_fee'])

        # check for 2 transfers
        transfers = 0
        for info in res['result']['vout']:
            if info['address'] == "AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK":
                transfers += 1
        self.assertEqual(2, transfers)

        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_sendmany_min_params(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address_to = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
        output = [{"asset": 'neo',
                   "value": 1,
                   "address": address_to},
                  {"asset": 'neo',
                   "value": 1,
                   "address": address_to}]
        with patch('neo.Network.nodemanager.NodeManager.relay', return_value=self.async_return(True)):
            req = self._gen_post_rpc_req("sendmany", params=[output])
            res = json.loads(self.do_test_post("/", json=req))

        self.assertEqual(res.get('jsonrpc', None), '2.0')
        self.assertIn('txid', res.get('result', {}).keys())
        self.assertIn('vin', res.get('result', {}).keys())
        self.assertIn("AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3", res['result']['vout'][2]['address'])
        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_sendmany_not_list(self):
        test_wallet_path = os.path.join(mkdtemp(), "sendfromaddress.db3")
        self.api_server.wallet = UserWallet.Create(
            test_wallet_path,
            to_aes_key('awesomepassword')
        )
        req = self._gen_post_rpc_req("sendmany", params=["arg"])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")
        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(test_wallet_path)

    def test_sendmany_too_many_args(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address_to = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
        output = [{"asset": 'neo',
                   "value": 1,
                   "address": address_to},
                  {"asset": 'neo',
                   "value": 1,
                   "address": address_to}]
        req = self._gen_post_rpc_req("sendmany", params=[output, 1, "APRgMZHZubii29UXF9uFa6sohrsYupNAvx", "arg"])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")
        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_sendmany_bad_assetid(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address_to = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
        output = [{"asset": 'neo',
                   "value": 1,
                   "address": address_to},
                  {"asset": 'ne',
                   "value": 1,
                   "address": address_to}]
        req = self._gen_post_rpc_req("sendmany", params=[output])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")
        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_sendmany_bad_address(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address_to = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaX'  # "AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaX" is too short causing ToScriptHash to fail
        output = [{"asset": 'neo',
                   "value": 1,
                   "address": address_to},
                  {"asset": 'neo',
                   "value": 1,
                   "address": address_to}]
        req = self._gen_post_rpc_req("sendmany", params=[output])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")
        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_sendmany_negative_amount(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address_to = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
        output = [{"asset": 'neo',
                   "value": 1,
                   "address": address_to},
                  {"asset": 'neo',
                   "value": -1,
                   "address": address_to}]
        req = self._gen_post_rpc_req("sendmany", params=[output])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")
        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_sendmany_zero_amount(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address_to = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
        output = [{"asset": 'neo',
                   "value": 1,
                   "address": address_to},
                  {"asset": 'neo',
                   "value": 0,
                   "address": address_to}]
        req = self._gen_post_rpc_req("sendmany", params=[output])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")
        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_sendmany_negative_fee(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address_to = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
        output = [{"asset": 'neo',
                   "value": 1,
                   "address": address_to},
                  {"asset": 'neo',
                   "value": 1,
                   "address": address_to}]
        req = self._gen_post_rpc_req("sendmany", params=[output, -0.005, "APRgMZHZubii29UXF9uFa6sohrsYupNAvx"])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")
        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_sendmany_bad_change_address(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address_to = "AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK"
        change_addr = "APRgMZHZubii29UXF9uFa6sohrsYupNAv"  # "APRgMZHZubii29UXF9uFa6sohrsYupNAv" is too short causing ToScriptHash to fail
        output = [{"asset": 'neo',
                   "value": 1,
                   "address": address_to},
                  {"asset": 'neo',
                   "value": 1,
                   "address": address_to}]
        req = self._gen_post_rpc_req("sendmany", params=[output, 0.005, change_addr])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -32602)
        self.assertEqual(error.get('message', None), "Invalid params")
        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_sendmany_insufficient_funds(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.api_server.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        address_to = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
        output = [{"asset": 'neo',
                   "value": 51,
                   "address": address_to},
                  {"asset": 'neo',
                   "value": 1,
                   "address": address_to}]
        req = self._gen_post_rpc_req("sendmany", params=[output])
        res = json.loads(self.do_test_post("/", json=req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -300)
        self.assertEqual(error.get('message', None), "Insufficient funds")
        self.api_server.wallet.Close()
        self.api_server.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_sendmany_fails_to_sign_tx(self):
        with patch('neo.Implementations.Wallets.peewee.UserWallet.UserWallet.Sign', return_value='False'):
            test_wallet_path = shutil.copyfile(
                WalletFixtureTestCase.wallet_1_path(),
                WalletFixtureTestCase.wallet_1_dest()
            )
            self.api_server.wallet = UserWallet.Open(
                test_wallet_path,
                to_aes_key(WalletFixtureTestCase.wallet_1_pass())
            )
            address_to = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
            output = [{"asset": 'neo',
                       "value": 1,
                       "address": address_to},
                      {"asset": 'neo',
                       "value": 1,
                       "address": address_to}]
            req = self._gen_post_rpc_req("sendmany", params=[output])
            res = json.loads(self.do_test_post("/", json=req))
            self.assertEqual(res.get('jsonrpc', None), '2.0')
            self.assertIn('type', res.get('result', {}).keys())
            self.assertIn('hex', res.get('result', {}).keys())
            self.api_server.wallet.Close()
            self.api_server.wallet = None
            os.remove(WalletFixtureTestCase.wallet_1_dest())

    def test_getblockheader_int(self):
        req = self._gen_post_rpc_req("getblockheader", params=[10, 1])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result']['index'], 10)
        self.assertEqual(res['result']['hash'], '0xd69e7a1f62225a35fed91ca578f33447d93fa0fd2b2f662b957e19c38c1dab1e')
        self.assertEqual(res['result']['confirmations'], GetBlockchain().Height - 10 + 1)
        self.assertEqual(res['result']['nextblockhash'], '0x2b1c78633dae7ab81f64362e0828153079a17b018d779d0406491f84c27b086f')

    def test_getblockheader_hash(self):
        req = self._gen_post_rpc_req("getblockheader", params=['2b1c78633dae7ab81f64362e0828153079a17b018d779d0406491f84c27b086f', 1])
        res = json.loads(self.do_test_post("/", json=req))

        self.assertEqual(res['result']['index'], 11)
        self.assertEqual(res['result']['confirmations'], GetBlockchain().Height - 11 + 1)
        self.assertEqual(res['result']['previousblockhash'], '0xd69e7a1f62225a35fed91ca578f33447d93fa0fd2b2f662b957e19c38c1dab1e')

    def test_getblockheader_hash_0x(self):
        req = self._gen_post_rpc_req("getblockheader", params=['0x2b1c78633dae7ab81f64362e0828153079a17b018d779d0406491f84c27b086f', 1])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result']['index'], 11)

    def test_getblockheader_hash_failure(self):
        req = self._gen_post_rpc_req("getblockheader", params=[GetBlockchain().Height + 1, 1])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertTrue('error' in res)
        self.assertEqual(res['error']['message'], 'Unknown block')

    def test_getblockheader_non_verbose(self):
        req = self._gen_post_rpc_req("getblockheader", params=[11, 0])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertIsNotNone(res['result'])

        # we should be able to instantiate a matching block with the result
        output = binascii.unhexlify(res['result'])
        blockheader = Helper.AsSerializableWithType(output, 'neo.Core.Header.Header')
        self.assertEqual(blockheader.Index, 11)
        self.assertEqual(str(blockheader.Hash), GetBlockchain().GetBlockHash(11).decode('utf8'))

    def test_gettransactionheight(self):
        txid = 'f999c36145a41306c846ea80290416143e8e856559818065be3f4e143c60e43a'
        req = self._gen_post_rpc_req("gettransactionheight", params=[txid])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(9448, res['result'])

    def test_gettransactionheight_invalid_hash(self):
        txid = 'invalid_tx_id'
        req = self._gen_post_rpc_req("gettransactionheight", params=[txid])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertTrue('error' in res)
        self.assertEqual(res['error']['message'], 'Unknown transaction')

    def test_gettransactionheight_invalid_hash2(self):
        txid = 'a' * 64  # something the right length but unknown
        req = self._gen_post_rpc_req("gettransactionheight", params=[txid])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertTrue('error' in res)
        self.assertEqual(res['error']['message'], 'Unknown transaction')
