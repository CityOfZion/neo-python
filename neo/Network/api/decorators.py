import json

from functools import wraps
# don't change this to log_manager, only used in the rest server example that also relies on logging to a file
from logzero import logger


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


def gen_authenticated_decorator(api_tokens=[]):
    """
    This is a helper to build an `@authenticated` decorator that knows which
    API tokens are allowed.

    Example usage which allows 2 valid API tokens:

        authenticated = gen_authenticated_decorator(['123', 'abc'])

        @authenticated
        def test(request):
            return { "hello": "world" }

    """
    if isinstance(api_tokens, (list, tuple)):
        pass
    elif isinstance(api_tokens, str):
        api_tokens = [api_tokens]
    else:
        raise Exception("Invalid data type for `api_tokens`: %s. Must be list, tuple or string" % type(api_tokens))

    # The normal @authenticated decorator, which accesses `api_tokens`
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
            if not user_auth_token.startswith("Bearer "):
                request.setHeader('Content-Type', 'application/json')
                request.setResponseCode(403)
                return json.dumps({"error": "No valid Authorization header found"})

            token = user_auth_token[7:]
            if token not in api_tokens:
                request.setHeader('Content-Type', 'application/json')
                request.setResponseCode(403)
                return json.dumps({"error": "Not authorized"})

            # If all good, proceed to request handler
            return func(request, *args, **kwargs)

        return wrapper

    # Return the decorator itself
    return authenticated
