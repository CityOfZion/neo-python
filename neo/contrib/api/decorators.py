import os
import json

from functools import wraps
from logzero import logger


# Get the API token from an environment variable
API_AUTH_TOKEN = os.getenv("NEO_REST_API_TOKEN", None)
if not API_AUTH_TOKEN:
    raise Exception("No NEO_REST_API_TOKEN environment variable found!")


def json_response(func):
    """
    @json_response decorator adds response header for content type,
    and json-dumps response object.

    Example usage:

        @json_response
        def test(request):
            return { "hello": "world" }
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        res = func(request, *args, **kwargs)
        request.setHeader('Content-Type', 'application/json')
        return json.dumps(res)
    return wrapper


def authenticated(func):
    """
    @authenticated decorator, which makes sure the HTTP request has the correct access token.
    Header has to be in the format "Authorization: Bearer {token}"

    If no valid header is part of the request's HTTP headers, this decorator automatically
    returns the HTTP status code 403.
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        # Make sure Authorization header is present
        if not request.requestHeaders.hasHeader("Authorization"):
            request.setHeader('Content-Type', 'application/json')
            request.setResponseCode(403)
            return json.dumps({"error": "No Authorization header found"})

        # Make sure Authorization header is valid
        user_auth_token = str(request.requestHeaders.getRawHeaders("Authorization")[0])
        if user_auth_token != "Bearer %s" % API_AUTH_TOKEN:
            request.setHeader('Content-Type', 'application/json')
            request.setResponseCode(403)
            return json.dumps({"error": "Invalid Authorization header"})

        # If all good, proceed to request handler
        return func(request, *args, **kwargs)
    return wrapper


def catch_exceptions(func):
    """
    @catch_exceptions decorator handles generic exceptions in the request handler.
    All uncaught exceptions will be packaged into a nice JSON response, and returned
    to the caller with status code 500.

    This is especially useful for development, for production you might want to
    disable the messages.
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            res = func(request, *args, **kwargs)
        except Exception as e:
            logger.exception(e)
            request.setResponseCode(500)
            request.setHeader('Content-Type', 'application/json')
            return json.dumps({"error": str(e)})
        return res
    return wrapper
