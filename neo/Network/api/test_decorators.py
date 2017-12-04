import json
from neo.Utils.NeoTestCase import NeoTestCase

from neo.Network.api.decorators import json_response, catch_exceptions, gen_authenticated_decorator


class DummyReqHeaders:
    headers = {}

    def hasHeader(self, key):
        return key in self.headers

    def getRawHeaders(self, key):
        return self.headers[key]


class DummyReq:
    headers = {}
    responseCode = None
    requestHeaders = DummyReqHeaders()

    def setHeader(self, key, val):
        self.headers[key] = val
        self.requestHeaders.headers[key] = [val]

    def setResponseCode(self, responseCode):
        assert type(responseCode) == int
        self.responseCode = responseCode


class Fixed8TestCase(NeoTestCase):
    def test_json_response(self):
        # @json_response converts an object to a string and sets the header

        @json_response
        def _test(request):
            return {"test": 123}

        _req = DummyReq()
        _res = _test(_req)
        self.assertEqual(type(_res), str)
        self.assertEqual(_req.headers["Content-Type"], "application/json")

    def test_catch_exceptions(self):
        @catch_exceptions
        def _test(request):
            1 / 0

        _req = DummyReq()

        print("This test should produce an error message")
        _res = _test(_req)
        _res_obj = json.loads(_res)
        self.assertEqual(_res_obj["error"], "division by zero")
        self.assertEqual(_req.headers["Content-Type"], "application/json")

    def test_gen_authenticated_decorator(self):
        authenticated = gen_authenticated_decorator("123")

        @authenticated
        def _test(request):
            return 123

        _req = DummyReq()
        _req.setHeader("Authorization", "Bearer 123")
        _res = _test(_req)
        self.assertEqual(_res, 123)
        self.assertEqual(_req.headers["Content-Type"], "application/json")
