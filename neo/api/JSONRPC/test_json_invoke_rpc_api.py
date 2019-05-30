"""
Run only thse tests:

    $ python -m unittest neo.api.JSONRPC.test_json_rpc_api
"""
import json
import os

from aiohttp.test_utils import AioHTTPTestCase

from neo.Settings import settings
from neo.SmartContract.ContractParameter import ContractParameter
from neo.SmartContract.ContractParameterType import ContractParameterType
from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.VM import VMState
from neo.VM.VMState import VMStateStr
from neo.api.JSONRPC.JsonRpcApi import JsonRpcApi


class JsonRpcInvokeApiTestCase(BlockchainFixtureTestCase, AioHTTPTestCase):

    def __init__(self, *args, **kwargs):
        super(JsonRpcInvokeApiTestCase, self).__init__(*args, **kwargs)
        self.api_server = JsonRpcApi()

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

    @classmethod
    def leveldb_testpath(cls):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

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
        return ret

    def test_invoke_1(self):
        # test POST requests
        contract_hash = 'b9fbcff6e50fd381160b822207231233dd3c56c2'
        jsn = [
            {
                'type': str(ContractParameterType.String),
                'value': 'name'
            },
            {
                'type': str(ContractParameterType.Array),
                'value': []
            }
        ]
        req = self._gen_post_rpc_req("invoke", params=[contract_hash, jsn])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result']['state'], VMStateStr(VMState.HALT))
        self.assertEqual(res['result']['gas_consumed'], '0.128')
        results = []
        for p in res['result']['stack']:
            results.append(ContractParameter.FromJson(p))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].Type, ContractParameterType.ByteArray)
        self.assertEqual(results[0].Value, bytearray(b'NEX Template V2'))

        # test GET requests
        url = self._gen_get_rpc_req("invoke", params=[contract_hash, jsn])
        res = json.loads(self.do_test_get(url))
        self.assertEqual(res['result']['state'], VMStateStr(VMState.HALT))
        self.assertEqual(res['result']['gas_consumed'], '0.128')
        results = []
        for p in res['result']['stack']:
            results.append(ContractParameter.FromJson(p))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].Type, ContractParameterType.ByteArray)
        self.assertEqual(results[0].Value, bytearray(b'NEX Template V2'))

    def test_invoke_2(self):
        contract_hash = 'b9fbcff6e50fd381160b822207231233dd3c56c2'
        jsn = [
            {
                'type': str(ContractParameterType.String),
                'value': 'balanceOf'
            },
            {
                'type': str(ContractParameterType.Array),
                'value': [
                    {
                        'type': str(ContractParameterType.ByteArray),
                        'value': bytearray(b'#\xba\'\x03\xc52c\xe8\xd6\xe5"\xdc2 39\xdc\xd8\xee\xe9').hex()
                    }
                ]
            }
        ]
        req = self._gen_post_rpc_req("invoke", params=[contract_hash, jsn])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result']['state'], VMStateStr(VMState.HALT))
        results = []
        for p in res['result']['stack']:
            results.append(ContractParameter.FromJson(p))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].Type, ContractParameterType.ByteArray)
        self.assertEqual(results[0].Value, bytearray(b'\x00\x90\x8c\xd4v\xe2\x00'))

    def test_invoke_3(self):
        contract_hash = 'b9fbcff6e50fd381160b822207231233dd3c56c2'
        req = self._gen_post_rpc_req("invokefunction", params=[contract_hash, 'symbol'])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result']['state'], VMStateStr(VMState.HALT))
        results = []
        for p in res['result']['stack']:
            results.append(ContractParameter.FromJson(p))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].Type, ContractParameterType.ByteArray)
        self.assertEqual(results[0].Value, bytearray(b'NXT2'))

    def test_invoke_4(self):
        contract_hash = 'b9fbcff6e50fd381160b822207231233dd3c56c2'
        params = [{'type': str(ContractParameterType.ByteArray),
                   'value': bytearray(b'#\xba\'\x03\xc52c\xe8\xd6\xe5"\xdc2 39\xdc\xd8\xee\xe9').hex()}]

        req = self._gen_post_rpc_req("invokefunction", params=[contract_hash, 'balanceOf', params])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result']['state'], VMStateStr(VMState.HALT))
        results = []
        for p in res['result']['stack']:
            results.append(ContractParameter.FromJson(p))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].Type, ContractParameterType.ByteArray)
        self.assertEqual(results[0].Value, bytearray(b'\x00\x90\x8c\xd4v\xe2\x00'))

    def test_invoke_5(self):
        test_script = "00046e616d6567c2563cdd3312230722820b1681d30fe5f6cffbb9000673796d626f6c67c2563cdd3312230722820b1681d30fe5f6cffbb90008646563696d616c7367c2563cdd3312230722820b1681d30fe5f6cffbb9"

        req = self._gen_post_rpc_req("invokescript", params=[test_script])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertEqual(res['result']['state'], VMStateStr(VMState.HALT))

        results = []
        for p in res['result']['stack']:
            results.append(ContractParameter.FromJson(p))

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].Value, bytearray(b'NEX Template V2'))
        self.assertEqual(results[1].Value, bytearray(b'NXT2'))
        self.assertEqual(results[2].Value, 8)

    def test_bad_invoke_script(self):
        test_script = '0zzzzzzef3e30b007cd98d67d7'
        req = self._gen_post_rpc_req("invokescript", params=[test_script])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertTrue('error' in res)
        self.assertIn('Non-hexadecimal digit found', res['error']['message'])

    def test_bad_invoke_script_2(self):
        test_script = '00046e616d656754a64cac1b103e662933ef3e30b007cd98d67d7000673796d626f6c6754a64cac1b1073e662933ef3e30b007cd98d67d70008646563696d616c736754a64cac1b1073e662933ef3e30b007cd98d67d7'
        req = self._gen_post_rpc_req("invokescript", params=[test_script])
        res = json.loads(self.do_test_post("/", json=req))
        self.assertTrue('error' in res)
        self.assertIn('Odd-length string', res['error']['message'])
