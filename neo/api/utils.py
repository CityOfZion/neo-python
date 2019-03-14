import json
import gzip
from functools import wraps
from aiohttp import web
from aiohttp.web_response import ContentCoding

COMPRESS_FASTEST = 1
BASE_STRING_SIZE = 49
MTU_TCP_PACKET_SIZE = 1500
COMPRESS_THRESHOLD = MTU_TCP_PACKET_SIZE + BASE_STRING_SIZE


# @json_response decorator for class methods
def json_response(func):
    """ @json_response decorator adds header and dumps response object """

    @wraps(func)
    async def wrapper(self, request, *args, **kwargs):
        res = await func(self, request, *args, **kwargs)
        response = web.json_response(data=res)
        if response.content_length > COMPRESS_THRESHOLD:
            response.enable_compress(force=ContentCoding.gzip)
        return response

    return wrapper


# @cors_header decorator to add the CORS headers
def cors_header(func):
    """ @cors_header decorator adds CORS headers """

    # TODO: update to work with aiohttp or use a cors header plugin
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        res = func(self, request, *args, **kwargs)
        request.setHeader('Access-Control-Allow-Origin', '*')
        request.setHeader('Access-Control-Allow-Headers', 'Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With')
        return res

    return wrapper
