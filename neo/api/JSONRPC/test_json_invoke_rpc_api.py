"""
Run only thse tests:

    $ python -m unittest neo.api.JSONRPC.test_json_rpc_api
"""
import json
import pprint
import binascii
import os
from klein.test.test_resource import requestMock
from twisted.web import server
from twisted.web.test.test_web import DummyChannel

from neo import __version__
from neo.api.JSONRPC.JsonRpcApi import JsonRpcApi
from neo.Utils.BlockchainFixtureTestCase import BlockchainFixtureTestCase
from neo.IO.Helper import Helper
from neo.SmartContract.ContractParameter import ContractParameter
from neo.SmartContract.ContractParameterType import ContractParameterType
from neocore.UInt160 import UInt160
from neo.VM import VMState
from neo.VM.VMState import VMStateStr
from neo.Settings import settings


def mock_post_request(body):
    return requestMock(path=b'/', method=b"POST", body=body)


def mock_get_request(path, method=b"GET"):
    request = server.Request(DummyChannel(), False)
    request.uri = path
    request.method = method
    request.clientproto = b'HTTP/1.1'
    return request


class JsonRpcInvokeApiTestCase(BlockchainFixtureTestCase):
    app = None  # type:JsonRpcApi

    @classmethod
    def leveldb_testpath(cls):
        return os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_chain')

    def setUp(self):
        self.app = JsonRpcApi(9479)

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
        mock_req = mock_post_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result']['state'], VMStateStr(VMState.HALT + VMState.BREAK))
        self.assertEqual(res['result']['gas_consumed'], '0.128')
        results = []
        for p in res['result']['stack']:
            results.append(ContractParameter.FromJson(p))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].Type, ContractParameterType.ByteArray)
        self.assertEqual(results[0].Value, bytearray(b'NEX Template V2'))

        # test GET requests
        req = self._gen_get_rpc_req("invoke", params=[contract_hash, jsn])
        mock_req = mock_get_request(req)
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result']['state'], VMStateStr(VMState.HALT + VMState.BREAK))
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
        mock_req = mock_post_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result']['state'], VMStateStr(VMState.HALT + VMState.BREAK))
        results = []
        for p in res['result']['stack']:
            results.append(ContractParameter.FromJson(p))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].Type, ContractParameterType.ByteArray)
        self.assertEqual(results[0].Value, bytearray(b'\x00\x90\x8c\xd4v\xe2\x00'))

    def test_invoke_3(self):
        contract_hash = 'b9fbcff6e50fd381160b822207231233dd3c56c2'
        req = self._gen_post_rpc_req("invokefunction", params=[contract_hash, 'symbol'])
        mock_req = mock_post_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result']['state'], VMStateStr(VMState.HALT + VMState.BREAK))
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
        mock_req = mock_post_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result']['state'], VMStateStr(VMState.HALT + VMState.BREAK))
        results = []
        for p in res['result']['stack']:
            results.append(ContractParameter.FromJson(p))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].Type, ContractParameterType.ByteArray)
        self.assertEqual(results[0].Value, bytearray(b'\x00\x90\x8c\xd4v\xe2\x00'))

    def test_invoke_5(self):
        test_script = "00046e616d6567c2563cdd3312230722820b1681d30fe5f6cffbb9000673796d626f6c67c2563cdd3312230722820b1681d30fe5f6cffbb90008646563696d616c7367c2563cdd3312230722820b1681d30fe5f6cffbb9" 

        req = self._gen_post_rpc_req("invokescript", params=[test_script])
        mock_req = mock_post_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res['result']['state'], VMStateStr(VMState.HALT + VMState.BREAK))

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
        mock_req = mock_post_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertTrue('error' in res)
        self.assertIn('Non-hexadecimal digit found', res['error']['message'])

    def test_bad_invoke_script_2(self):
        test_script = '00046e616d656754a64cac1b103e662933ef3e30b007cd98d67d7000673796d626f6c6754a64cac1b1073e662933ef3e30b007cd98d67d70008646563696d616c736754a64cac1b1073e662933ef3e30b007cd98d67d7'
        req = self._gen_post_rpc_req("invokescript", params=[test_script])
        mock_req = mock_post_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertTrue('error' in res)
        self.assertIn('Odd-length string', res['error']['message'])
