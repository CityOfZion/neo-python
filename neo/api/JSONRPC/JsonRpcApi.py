"""
The JSON-RPC API is using the Python package 'klein', which makes it possible to
create HTTP routes and handlers with Twisted in a similar style to Flask:
https://github.com/twisted/klein

See also:
* http://www.jsonrpc.org/specification
"""
import json
from json.decoder import JSONDecodeError

from klein import Klein
from logzero import logger

from neo import __version__
from neo.Core.Blockchain import Blockchain
from neo.api.utils import json_response
from neo.Core.State.AccountState import AccountState
from neo.Core.State.ContractState import ContractState
from neocore.UInt160 import UInt160
from neocore.UInt256 import UInt256
from neo.Wallets import Wallet
from neo.Core.Helper import Helper
from neo.Network.NodeLeader import NodeLeader


class JsonRpcError(Exception):
    """
    Easy error handling throughout the handlers. Allows for easy code overrides
    to be compliant with neo-cli responses
    """
    # standard json-rpc errors as per spec: http://www.jsonrpc.org/specification
    # PARSE_ERROR = {"code": -32700, "message": "Parse error"}
    # INVALID_REQUEST = {"code": -32600, "message": "Invalid Request"}
    # METHOD_NOT_FOUND = {"code": -32601, "message": "Method not found"}
    # INVALID_PARAMS = {"code": -32602, "message": "Invalid params"}
    # INTERNAL_ERROR = {"code": -32603, "message": "Internal error"}
    # SERVER_ERROR = {"code": -32000, "message": "Server error"}

    message = None
    code = None

    def __init__(self, code, message):
        super(JsonRpcError, self).__init__(message)
        self.code = code
        self.message = message

    @staticmethod
    def parseError(message=None):
        return JsonRpcError(-32700, message or "Parse error")

    @staticmethod
    def methodNotFound(message=None):
        return JsonRpcError(-32601, message or "Method not found")

    @staticmethod
    def invalidRequest(message=None):
        return JsonRpcError(-32600, message or "Invalid Request")

    @staticmethod
    def internalError(message=None):
        return JsonRpcError(-32603, message or "Internal error")


class JsonRpcApi(object):
    app = Klein()
    port = None

    def __init__(self, port):
        self.port = port

    #
    # JSON-RPC API Route
    #
    @app.route('/')
    @json_response
    def home(self, request):
        # {"jsonrpc": "2.0", "id": 5, "method": "getblockcount", "params": []}
        body = None
        request_id = None

        try:
            body = json.loads(request.content.read().decode("utf-8"))
            request_id = body["id"] if body and "id" in body else None

            if "jsonrpc" not in body or body["jsonrpc"] != "2.0":
                raise JsonRpcError.invalidRequest("Invalid value for 'jsonrpc'")

            if "id" not in body:
                raise JsonRpcError.invalidRequest("Field 'id' is missing")

            if "method" not in body:
                raise JsonRpcError.invalidRequest("Field 'method' is missing")

            params = body["params"] if "params" in body else None
            result = self.json_rpc_method_handler(body["method"], params)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }

        except JSONDecodeError as e:
            error = JsonRpcError.parseError()
            return self.get_custom_error_payload(request_id, error.code, error.message)

        except JsonRpcError as e:
            return self.get_custom_error_payload(request_id, e.code, e.message)

        except Exception as e:
            error = JsonRpcError.internalError(str(e))
            return self.get_custom_error_payload(request_id, error.code, error.message)

    def get_custom_error_payload(self, request_id, code, message):
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }

    def json_rpc_method_handler(self, method, params):
        # print("method", method, params)

        if method == "getaccountstate":
            acct = Blockchain.Default().GetAccountState(params[0])
            if acct is None:
                try:
                    acct = AccountState(script_hash=Helper.AddrStrToScriptHash(params[0]))
                except Exception as e:
                    raise JsonRpcError(-2146233033, "One of the identified items was in an invalid format.")

            return acct.ToJson()

        elif method == "getassetstate":
            asset_id = params[0].encode('utf-8')
            asset = Blockchain.Default().GetAssetState(asset_id)
            if asset:
                return asset.ToJson()
            raise JsonRpcError(-100, "Unknown asset")

        elif method == "getbestblockhash":
            return Blockchain.Default().CurrentHeaderHash.decode('utf-8')

        elif method == "getblock":
            # this should work for either str or int
            block = Blockchain.Default().GetBlock(params[0])
            if not block:
                raise JsonRpcError(-100, "Unknown block")

            verbose = False
            if len(params) >= 2 and params[1]:
                verbose = True

            if verbose:
                jsn = block.ToJson()
                jsn['confirmations'] = Blockchain.Default().Height - block.Index + 1
                hash = Blockchain.Default().GetNextBlockHash(block.Hash)
                if hash:
                    jsn['nextblockhash'] = hash.decode('utf-8')
                return jsn

            # full tx data is not included by default
            # this will load them to be serialized
            block.Transactions = block.FullTransactions
            return Helper.ToArray(block).decode('utf-8')

        elif method == "getblockcount":
            return Blockchain.Default().Height + 1

        elif method == "getblockhash":
            height = params[0]
            if height >= 0 and height <= Blockchain.Default().Height:
                return Blockchain.Default().GetBlockHash(height).decode('utf-8')
            else:
                raise JsonRpcError(-100, "Invalid Height")

        elif method == "getblocksysfee":
            height = params[0]
            if height >= 0 and height <= Blockchain.Default().Height:
                return Blockchain.Default().GetSysFeeAmountByHeight(height)
            else:
                raise JsonRpcError(-100, "Invalid Height")

        elif method == "getconnectioncount":
            return len(NodeLeader.Instance().Peers)

        elif method == "getcontractstate":
            # TODO: cannot execute this query against the live nodes with a successful response
            raise NotImplementedError()
            # script_hash = params[0]
            # contract = Blockchain.Default().GetContract(script_hash)
            # if contract is None:
            #     raise JsonRpcError(-100, "Unknown contract")
            # else:
            #     return contract.ToJson()

        elif method == "getrawmempool":
            return list(map(lambda hash: hash.decode('utf-8'), NodeLeader.Instance().MemPool.keys()))

        elif method == "getversion":
            return {
                "port": self.port,
                "nonce": 771199013,  # TODO: make this the real nonce, currently taken straight from testnet neo-cli
                "useragent": "/neo-python:%s/" % __version__  # This ok, or should we mimic `/NEO:2.6.0/`?
            }

        elif method == "getrawtransaction":
            raise NotImplementedError()

        elif method == "getstorage":
            raise NotImplementedError()

        elif method == "gettxout":
            raise NotImplementedError()

        elif method == "invoke":
            raise NotImplementedError()

        elif method == "invokefunction":
            raise NotImplementedError()

        elif method == "invokescript":
            raise NotImplementedError()

        elif method == "sendrawtransaction":
            raise NotImplementedError()

        elif method == "submitblock":
            raise NotImplementedError()

        elif method == "validateaddress":
            raise NotImplementedError()

        elif method == "getpeers":
            raise NotImplementedError()

        raise JsonRpcError.methodNotFound()
