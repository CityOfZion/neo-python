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
from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB
from logzero import logger
from neo.Core.Blockchain import Blockchain
from neo.api.utils import json_response
import ast


class JsonRpcErrors:
    PARSE_ERROR = {"code": -32700, "message": "Parse error"}
    INVALID_REQUEST = {"code": -32600, "message": "Invalid Request"}
    METHOD_NOT_FOUND = {"code": -32601, "message": "Method not found"}
    INVALID_PARAMS = {"code": -32602, "message": "Invalid params"}
    INTERNAL_ERROR = {"code": -32603, "message": "Internal error"}
    SERVER_ERROR = {"code": -32000, "message": "Server error"}


class JsonRpcError(Exception):
    message = None
    json_rpc_error = None

    def __init__(self, message, json_rpc_error, json_rpc_error_code=None):
        super(JsonRpcError, self).__init__(message)
        self.message = message
        self.error_data = {"error_message": message}

        self.json_rpc_error = json_rpc_error
        if json_rpc_error_code:
            self.json_rpc_error["code"] = json_rpc_error_code


class JsonRpcApi(object):
    app = Klein()
    notif = None

    def __init__(self):
        self.notif = NotificationDB.instance()

    #
    # JSON-RPC API Route
    #
    @app.route('/')
    @json_response
    def home(self, request):
        # {"jsonrpc": "2.0", "id": 5, "method": "getblockcount", "params": []}
        body = None
        try:
            body = json.loads(request.content.read().decode("utf-8"))
            if "jsonrpc" not in body or body["jsonrpc"] != "2.0":
                raise JsonRpcError("Invalid value for 'jsonrpc'", JsonRpcErrors.INVALID_REQUEST)

            if "id" not in body:
                raise JsonRpcError("Field 'id' is missing", JsonRpcErrors.INVALID_REQUEST)

            if "method" not in body:
                raise JsonRpcError("Field 'method' is missing", JsonRpcErrors.INVALID_REQUEST)

            params = ast.literal_eval(body["params"]) if "params" in body else None
            result = self.json_rpc_method_handler(body["method"], params)
            return self.get_response(body["id"], result)

        except JSONDecodeError as e:
            request_id = body["id"] if body and "id" in body else None
            return self.get_error_payload(request_id, JsonRpcErrors.PARSE_ERROR, data={"error_message": str(e)})

        except JsonRpcError as e:
            request_id = body["id"] if body and "id" in body else None
            return self.get_error_payload(request_id, e.json_rpc_error, data=e.error_data)

        except Exception as e:
            request_id = body["id"] if body and "id" in body else None
            return self.get_error_payload(request_id, JsonRpcErrors.INTERNAL_ERROR, data={"error_message": str(e)})

    def get_response(self, request_id, result):
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }

    def get_error_payload(self, request_id, error, data=None, code=None):
        error_payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": error
        }

        if code:
            error_payload["error"]["code"] = code

        if data:
            error_payload["data"] = data

        return error_payload

    def json_rpc_method_handler(self, method, params):
        # print("method", method, params)
        if method == "getblockcount":
            return Blockchain.Default().HeaderHeight
        if method == "getblockhash":
            height = params[0]
            if height >= 0 and height <= Blockchain.Default().Height:
                return Blockchain.Default().GetBlockHash(height).decode('utf-8')

        raise JsonRpcError("Method '%s' not found" % method, JsonRpcErrors.METHOD_NOT_FOUND)
