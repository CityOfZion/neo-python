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
from neo.SmartContract.ContractParameter import ContractParameter
from neo.SmartContract.ContractParameterType import ContractParameterType
from neocore.UInt160 import UInt160
import binascii
from neo.VM import VMState


def mock_request(body):
    return requestMock(path=b'/', method="POST", body=body)


class JsonRpcInvokeApiTestCase(BlockchainFixtureTestCase):
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

    def test_invoke_1(self):
        contract_hash = 'd7678dd97c000be3f33e9362e673101bac4ca654'
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
        req = self._gen_rpc_req("invoke", params=[contract_hash, jsn])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result']['state'], VMState.HALT + VMState.BREAK)
        self.assertEqual(res['result']['gas_consumed'], '0.205')
        results = []
        for p in res['result']['stack']:
            results.append(ContractParameter.FromJson(p))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].Type, ContractParameterType.ByteArray)
        self.assertEqual(results[0].Value, bytearray(b'LOCALTOKEN'))

    def test_invoke_2(self):
        contract_hash = 'd7678dd97c000be3f33e9362e673101bac4ca654'
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
                        'value': bytearray(b'\xec\xa8\xfc\xf9Nz*\x7f\xc3\xfdT\xae\x0e\xd3\xd3MR\xec%\x90').hex()
                    }
                ]
            }
        ]
        req = self._gen_rpc_req("invoke", params=[contract_hash, jsn])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result']['state'], VMState.HALT + VMState.BREAK)
        results = []
        for p in res['result']['stack']:
            results.append(ContractParameter.FromJson(p))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].Type, ContractParameterType.ByteArray)
        self.assertEqual(results[0].Value, bytearray(b'\xe9\x0f\x80\xbb\x04\x90\x00'))

    def test_invoke_3(self):
        contract_hash = 'd7678dd97c000be3f33e9362e673101bac4ca654'
        req = self._gen_rpc_req("invokefunction", params=[contract_hash, 'symbol'])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result']['state'], VMState.HALT + VMState.BREAK)
        results = []
        for p in res['result']['stack']:
            results.append(ContractParameter.FromJson(p))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].Type, ContractParameterType.ByteArray)
        self.assertEqual(results[0].Value, bytearray(b'LWTF'))

    def test_invoke_4(self):
        contract_hash = 'd7678dd97c000be3f33e9362e673101bac4ca654'
        params = [{'type': str(ContractParameterType.ByteArray),
                   'value': bytearray(b'\xec\xa8\xfc\xf9Nz*\x7f\xc3\xfdT\xae\x0e\xd3\xd3MR\xec%\x90').hex()}]

        req = self._gen_rpc_req("invokefunction", params=[contract_hash, 'balanceOf', params])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result']['state'], VMState.HALT + VMState.BREAK)
        results = []
        for p in res['result']['stack']:
            results.append(ContractParameter.FromJson(p))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].Type, ContractParameterType.ByteArray)
        self.assertEqual(results[0].Value, bytearray(b'\xe9\x0f\x80\xbb\x04\x90\x00'))

    def test_invoke_5(self):
        test_script = '00046e616d656754a64cac1b1073e662933ef3e30b007cd98d67d7000673796d626f6c6754a64cac1b1073e662933ef3e30b007cd98d67d70008646563696d616c736754a64cac1b1073e662933ef3e30b007cd98d67d7'
        req = self._gen_rpc_req("invokescript", params=[test_script])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result']['state'], VMState.HALT + VMState.BREAK)

        results = []
        for p in res['result']['stack']:
            results.append(ContractParameter.FromJson(p))
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].Value, bytearray(b'LOCALTOKEN'))
        self.assertEqual(results[1].Value, bytearray(b'LWTF'))
        self.assertEqual(results[2].Value, 8)

    def test_bad_invoke_script(self):
        test_script = '0zzzzzzef3e30b007cd98d67d7'
        req = self._gen_rpc_req("invokescript", params=[test_script])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertTrue('error' in res)
        self.assertIn('Non-hexadecimal digit found', res['error']['message'])

    def test_bad_invoke_script_2(self):
        test_script = '00046e616d656754a64cac1b103e662933ef3e30b007cd98d67d7000673796d626f6c6754a64cac1b1073e662933ef3e30b007cd98d67d70008646563696d616c736754a64cac1b1073e662933ef3e30b007cd98d67d7'
        req = self._gen_rpc_req("invokescript", params=[test_script])
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertTrue('error' in res)
        self.assertIn('Odd-length string', res['error']['message'])
