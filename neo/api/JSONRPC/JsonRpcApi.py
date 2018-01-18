"""
The JSON-RPC API is using the Python package 'klein', which makes it possible to
create HTTP routes and handlers with Twisted in a similar style to Flask:
https://github.com/twisted/klein

See also:
* http://www.jsonrpc.org/specification
"""
import json
from json.decoder import JSONDecodeError
from functools import wraps

from klein import Klein
from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB
from logzero import logger
from neo.Core.Blockchain import Blockchain


class Errors:
    PARSE_ERROR = {"code": -32700, "message": "Parse error"}
    INVALID_REQUEST = {"code": -32600, "message": "Invalid Request"}
    METHOD_NOT_FOUND = {"code": -32601, "message": "Method not found"}
    INVALID_PARAMS = {"code": -32602, "message": "Invalid params"}
    INTERNAL_ERROR = {"code": -32603, "message": "Internal error"}
    INVALID_PARAMS = {"code": -32000, "message": "Server error"}


def json_response(func):
    """ @json_response decorator adds header and dumps response object """
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        res = func(self, request, *args, **kwargs)
        request.setHeader('Content-Type', 'application/json')
        return json.dumps(res) if isinstance(res, dict) else res
    return wrapper


class JsonRpcApi(object):
    app = Klein()
    notif = None

    def __init__(self):
        self.notif = NotificationDB.instance()

    #
    # JSON-RPC Route
    #
    @app.route('/')
    @json_response
    def home(self, request):
        # {"jsonrpc": "2.0", "id": 5, "method": "getblockcount", "params": []}
        try:
            body = json.loads(request.content.read().decode("utf-8"))

        except JSONDecodeError as e:
            return self.get_error_payload(None, Errors.PARSE_ERROR, data={"exception": str(e)})

        except Exception as e:
            return self.get_error_payload(None, Errors.INTERNAL_ERROR, data={"exception": str(e)})

    def get_error_payload(self, id, error, data=None, code=None):
        error_payload = {
            "jsonrpc": "2.0",
            "id": id,
            "error": error
        }

        if code:
            error_payload["error"]["code"] = code

        if data:
            error_payload["data"] = data

        return error_payload
