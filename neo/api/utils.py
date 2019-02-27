from aiohttp import web
from aiohttp.web_response import ContentCoding
from functools import wraps

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
            response.enable_compression(force=ContentCoding.gzip)
        return response

    return wrapper
