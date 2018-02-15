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
from neocore.UInt256 import UInt256
from neo.Blockchain import GetBlockchain
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
        self.assertEqual(758716, res["result"])

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

    def test_get_asset_state_0x(self):
        asset_str = '0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7'
        req = self._gen_rpc_req("getassetstate", params=[asset_str])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result']['assetId'], asset_str)

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
        self.assertEqual(res['result'], '0x748de6a3bcb6f3dc70c72a625f8057f83e876a1168c373423f524dec78706d25')

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
        self.assertEqual(res['result']['confirmations'], 758706)
        self.assertEqual(res['result']['nextblockhash'], '0xa0d34f68cb7a04d625ae095fa509479ec7dcb4dc87ecd865ab059d0f8a42decf')

    def test_get_block_hash(self):
        req = self._gen_rpc_req("getblock", params=['a0d34f68cb7a04d625ae095fa509479ec7dcb4dc87ecd865ab059d0f8a42decf', 1])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))

        self.assertEqual(res['result']['index'], 11)
        self.assertEqual(res['result']['confirmations'], 758705)
        self.assertEqual(res['result']['previousblockhash'], '0x9410bd44beb7d6febc9278b028158af2781fcfb40cf2c6067b3525d24eff19f6')

    def test_get_block_hash_0x(self):
        req = self._gen_rpc_req("getblock", params=['0xa0d34f68cb7a04d625ae095fa509479ec7dcb4dc87ecd865ab059d0f8a42decf', 1])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result']['index'], 11)

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

        # test negative block
        req = self._gen_rpc_req("getblocksysfee", params=[-1])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertTrue('error' in res)
        self.assertEqual(res['error']['message'], 'Invalid Height')

        # test block exceeding max block height
        req = self._gen_rpc_req("getblocksysfee", params=[3000000000])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertTrue('error' in res)
        self.assertEqual(res['error']['message'], 'Invalid Height')

    def test_block_non_verbose(self):
        req = self._gen_rpc_req("getblock", params=[2003, 0])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertIsNotNone(res['result'])

        # we should be able to instantiate a matching block with the result
        output = binascii.unhexlify(res['result'])
        block = Helper.AsSerializableWithType(output, 'neo.Core.Block.Block')
        self.assertEqual(block.Index, 2003)
        self.assertEqual(len(block.Transactions), 2)

    def test_get_contract_state(self):
        contract_hash = UInt160(data=bytearray(b'\x11\xc4\xd1\xf4\xfb\xa6\x19\xf2b\x88p\xd3n:\x97s\xe8tp[')).ToString()
        req = self._gen_rpc_req("getcontractstate", params=[contract_hash])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result']['code_version'], '3')
        self.assertEqual(res['result']['properties']['storage'], True)
        self.assertEqual(res['result']['code']['hash'], '0x5b7074e873973a6ed3708862f219a6fbf4d1c411')
        self.assertEqual(res['result']['code']['returntype'], 5)
        self.assertEqual(res['result']['code']['parameters'], '0710')

    def test_get_contract_state_0x(self):
        contract_hash = '0x%s' % UInt160(data=bytearray(b'\x11\xc4\xd1\xf4\xfb\xa6\x19\xf2b\x88p\xd3n:\x97s\xe8tp[')).ToString()
        req = self._gen_rpc_req("getcontractstate", params=[contract_hash])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result']['code_version'], '3')

    def test_get_contract_state_not_found(self):
        contract_hash = '0xf4e65b0e1ba449d8d0f3baae1690b455b0e6e75c'
        req = self._gen_rpc_req("getcontractstate", params=[contract_hash])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertTrue('error' in res)
        self.assertEqual(res['error']['message'], 'Unknown contract')

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

    def test_validate_address(self):
        # example from docs.neo.org
        req = self._gen_rpc_req("validateaddress", params=["AQVh2pG732YvtNaxEGkQUei3YA4cvo7d2i"])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertTrue(res["result"]["isvalid"])

        # example from docs.neo.org
        req = self._gen_rpc_req("validateaddress", params=["152f1muMCNa7goXYhYAQC61hxEgGacmncB"])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertFalse(res["result"]["isvalid"])

        # catch completely invalid argument
        req = self._gen_rpc_req("validateaddress", params=[])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertTrue('error' in res)
        self.assertEqual('Missing argument', res['error']['message'])

        # catch completely invalid argument
        req = self._gen_rpc_req("validateaddress", params=[""])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertTrue('error' in res)
        self.assertEqual('Missing argument', res['error']['message'])

    def test_getrawtx_1(self):
        txid = 'cedb5c4e24b1f6fc5b239f2d1049c3229ad5ed05293c696b3740dc236c3f41b4'
        req = self._gen_rpc_req("getrawtransaction", params=[txid, 1])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))['result']
        self.assertEqual(res['blockhash'], '0x41720c35f5f15e5dc343d67fb54ab1e3825de47b476b5ae56cede2bf30657fde')
        self.assertEqual(res['txid'], "0x%s" % txid)
        self.assertEqual(res['blocktime'], 1499393065)
        self.assertEqual(res['type'], 'ContractTransaction')

    def test_getrawtx_2(self):
        txid = 'cedb5c4e24b1f6fc5b239f2d1049c3229ad5ed05293c696b3740dc236c3f41b4'
        req = self._gen_rpc_req("getrawtransaction", params=[txid, 0])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))['result']
        expected = '800001f00431313131010206cc6f919695fb55c9605c55127128c29697d791af884c2636416c69a944880100029b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc500e1f50500000000e58e5999bcbf5d78f52ead40654131abb9ee27099b7cffdaa674beae0f930ebe6085af9093e5fe56b34a5c220ccdcf6efc336fc5009a04f516000000e53a27d37d7f5a3187003c21efe3725304a7410601414058b4a41beabdcf62381f7feea02767a714eb8ea49212fdb47a6f0bed2d0ae87d27377d9c2b4412ebf816042f2144e6e08939c7d83638b61208d3a7f5ea47c3ba232102ca81fa6c7ef20219c417d876c2743ea87728d416632d09c18004652aed09e000ac'
        self.assertEqual(res, expected)

    def test_getrawtx_3(self):
        txid = 'cedb5c4e24b1f6fc5b239f2d1049c3229ad5ed05293c696b3740dc236c3f41b3'
        req = self._gen_rpc_req("getrawtransaction", params=[txid, 0])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertTrue('error' in res)
        self.assertEqual(res['error']['message'], 'Unknown Transaction')

    def test_get_storage_item(self):
        contract_hash = '16f1559c3c27d66d087bef936804105457617c8a'
        storage_key = binascii.hexlify(b'totalSupply').decode('utf-8')
        req = self._gen_rpc_req("getstorage", params=[contract_hash, storage_key])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result'], '001843d5ba05')
        actual_val = int.from_bytes(binascii.unhexlify(res['result'].encode('utf-8')), 'little')
        self.assertEqual(actual_val, 6300000000000)

    def test_get_storage_item2(self):
        contract_hash = '0xd7678dd97c000be3f33e9362e673101bac4ca654'
        storage_key = binascii.hexlify(b'totalSupply').decode('utf-8')
        req = self._gen_rpc_req("getstorage", params=[contract_hash, storage_key])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result'], '0070723d14b200')

    def test_get_storage_item_key_not_found(self):
        contract_hash = '0xd7678dd97c000be3f33e9362e673101bac4ca654'
        storage_key = binascii.hexlify(b'blah').decode('utf-8')
        req = self._gen_rpc_req("getstorage", params=[contract_hash, storage_key])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result'], None)

    def test_get_storage_item_contract_not_found(self):
        contract_hash = '0xd7678dd97c100be3f33e9362e673101bac4ca654'
        storage_key = binascii.hexlify(b'blah').decode('utf-8')
        req = self._gen_rpc_req("getstorage", params=[contract_hash, storage_key])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result'], None)

    def test_get_storage_item_bad_contract_hash(self):
        contract_hash = '0xd7678dd97c000b3e9362e673101bac4ca654'
        storage_key = binascii.hexlify(b'blah').decode('utf-8')
        req = self._gen_rpc_req("getstorage", params=[contract_hash, storage_key])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertTrue('error' in res)
        self.assertIn('Invalid UInt', res['error']['message'])

    def test_get_unspents(self):
        u = UInt256.ParseString('0ff23561c611ccda65470c9a4a5f1be31f2f4f61b98c75d051e1a72e85a302eb')
        unspents = GetBlockchain().GetAllUnspent(u)
        self.assertEqual(len(unspents), 1)

    def test_gettxout(self):
        # block 730901 - 2 transactions
        # output with index 0 is spent, so should return an error

        txid = '0ff23561c611ccda65470c9a4a5f1be31f2f4f61b98c75d051e1a72e85a302eb'
        output_index = 0
        req = self._gen_rpc_req("gettxout", params=[txid, output_index])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        # will return `null` if not found
        self.assertEqual(None, res["result"])

        # output with index 1 is unspent, so should return valid values
        txid = '0ff23561c611ccda65470c9a4a5f1be31f2f4f61b98c75d051e1a72e85a302eb'
        output_index = 1
        req = self._gen_rpc_req("gettxout", params=[txid, output_index])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))

        expected_asset = '0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7'
        expected_value = "25"
        expected_address = 'AHYb3ySrHbhzouZ81ZMnCf8c7zYaoDg64x'

        self.assertEqual(output_index, res["result"]["n"])
        self.assertEqual(expected_address, res["result"]["address"])
        self.assertEqual(expected_asset, res["result"]["asset"])
        self.assertEqual(expected_value, res["result"]["value"])

        # now test for a different block (730848) with a floating value
        txid = '9c9f2c430c3cfb805e8c22d0a7778a60ce7792fad52ffe9b34f56de8e2c1d2e6'
        output_index = 1  # index 0 is spent, 0 is unspent
        req = self._gen_rpc_req("gettxout", params=[txid, output_index])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))

        expected_value = "2609.997813"
        self.assertEqual(output_index, res["result"]["n"])
        self.assertEqual(expected_value, res["result"]["value"])

    def test_send_raw_tx(self):
        raw_tx = '80000001b10ad9ec660bf343c0eb411f9e05b4fa4ad8abed31d4e4dc5bb6ae416af0c4de000002e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c60c8db571300000000af12a8687b14948bc4a008128a550a63695bc1a5e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c603808b44002000000eca8fcf94e7a2a7fc3fd54ae0ed3d34d52ec25900141404749ce868ed9588f604eeeb5c523db39fd57cd7f61d04393a1754c2d32f131d67e6b1ec561ac05012b7298eb5ff254487c76de0b2a0c4d097d17cec708c0a9802321025b5c8cdcb32f8e278e111a0bf58ebb463988024bb4e250aa4310b40252030b60ac'
        req = self._gen_rpc_req("sendrawtransaction", params=[raw_tx])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result'], True)

    def test_send_raw_tx_bad(self):
        raw_tx = '80000001b10ad9ec660bf343c0eb411f9e05b4fa4ad8abed31d4e4dc5bb6ae416af0c4de000002e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c60c8db571300000000af12a8687b14948bc4a008128a550a63695bc1a5e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c603808b44002000000eca8fcf94e7a2a7fc3fd54ae0ed3d34d52ec25900141404749ce868ed9588f604eeeb5c523db39fd57cd7f61d04393a1754c2d32f131d67e6b1ec561ac05012b7298eb5ff254487c76de0b2a0c4d097d17cec708c0a9802321025b5c8cdcb32f8e278e111a0bf58ebb463988024bb4e250aa4310b40252030b60ac'
        req = self._gen_rpc_req("sendrawtransaction", params=[raw_tx])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result'], False)

    def test_send_raw_tx_bad_2(self):
        raw_tx = '80000001b10ad9ec660bf343c0eb411f9e05b4fa4ad8abed31d4e4dc5bb6ae416af0c4de000002e72d286979ee6cbb7e65dfddfb2e384100b8d148e7758de42e4168b71792c60c8db571300000000af12a8687b14948bc4a008128a550a63695bc1a5e72d286979ee6cb1b7e65dfddfb2e384100b8d148e7758de42e4168b71792c603808b44002000000eca8fcf94e7a2a7fc3fd54ae0ed3d34d52ec25900141404749ce868ed9588f604eeeb5c523db39fd57cd7f61d04393a1754c2d32f131d67e6b1ec561ac05012b7298eb5ff254487c76de0b2a0c4d097d17cec708c0a9802321025b5c8cdcb32f8e278e111a0bf58ebb463988024bb4e250aa4310b40252030b60ac'
        req = self._gen_rpc_req("sendrawtransaction", params=[raw_tx])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertTrue('error' in res)
        self.assertEqual(res['error']['code'], -32603)
