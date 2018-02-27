import json
from functools import wraps


# @json_response decorator for class methods
def json_response(func):
    """ @json_response decorator adds header and dumps response object """
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        res = func(self, request, *args, **kwargs)
        request.setHeader('Content-Type', 'application/json')
        return json.dumps(res) if isinstance(res, dict) else res
    return wrapper


# @cors_header decorator to add the CORS headers
def cors_header(func):
    """ @cors_header decorator adds CORS headers """
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        res = func(self, request, *args, **kwargs)
        request.setHeader('Access-Control-Allow-Origin', '*')
        return res
    return wrapper
