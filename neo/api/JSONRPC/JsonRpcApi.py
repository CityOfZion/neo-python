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
            return self.get_custom_error_payload(request_id, JsonRpcError.INTERNAL_ERROR["code"], str(e))

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
        if method == "getblockcount":
            return Blockchain.Default().HeaderHeight
        elif method == "getblockhash":
            height = params[0]
            if height >= 0 and height <= Blockchain.Default().Height:
                return Blockchain.Default().GetBlockHash(height).decode('utf-8')
            else:
                raise JsonRpcError(-100, "Invalid Height")

        raise JsonRpcError.methodNotFound()
