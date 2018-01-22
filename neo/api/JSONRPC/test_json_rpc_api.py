"""
python -m unittest neo.api.JSONRPC.test_json_rpc_api
"""
import json
import os
import requests
import tarfile
import logzero
import shutil
from unittest import TestCase
from klein.test.test_resource import requestMock

from neo.Settings import settings
from neo.api.JSONRPC.JsonRpcApi import JsonRpcApi
from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB
from neocore.UInt160 import UInt160


def mock_request(body):
    return requestMock(path=b'/', method="POST", body=body)


class JsonRpcApiTestCase(TestCase):
    FIXTURE_REMOTE_LOC = 'https://s3.us-east-2.amazonaws.com/cityofzion/fixtures/notif_fixture.tar.gz'
    FIXTURE_FILENAME = './Chains/notif_fixture.tar.gz'
    NOTIFICATION_DB_NAME = 'fixtures/test_notifications'

    app = None  # type:JsonRpcApi

    @classmethod
    def setUpClass(cls):
        if not os.path.exists(cls.FIXTURE_FILENAME):
            logzero.logger.info(
                "downloading fixture notification database from %s. this may take a while" % cls.FIXTURE_REMOTE_LOC)

            response = requests.get(cls.FIXTURE_REMOTE_LOC, stream=True)

            response.raise_for_status()
            with open(cls.FIXTURE_FILENAME, 'wb+') as handle:
                for block in response.iter_content(1024):
                    handle.write(block)

        try:
            tar = tarfile.open(cls.FIXTURE_FILENAME)
            tar.extractall()
            tar.close()
        except Exception as e:
            raise Exception("Could not extract tar file - %s. You may want need to remove the fixtures file %s manually to fix this." % (e, cls.FIXTURE_FILENAME))

        if not os.path.exists(cls.NOTIFICATION_DB_NAME):
            raise Exception("Error downloading fixtures")

        settings.NOTIFICATION_DB_PATH = cls.NOTIFICATION_DB_NAME
        ndb = NotificationDB.instance()
        ndb.start()

    @classmethod
    def tearDownClass(cls):
        NotificationDB.instance().close()
        shutil.rmtree(cls.NOTIFICATION_DB_NAME)

    def setUp(self):
        self.app = JsonRpcApi()

    # def test_1_ok(self):

    #     ndb = NotificationDB.instance()

    #     events = ndb.get_by_block(206939)

    #     self.assertEqual(len(events), 1)

    # def test_2_klein_app(self):

    #     self.assertIsNotNone(self.app.notif)

    def test_invalid_json_payload(self):
        mock_req = mock_request(b"{ invalid")
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["error"]["code"], -32700)

        mock_req = mock_request(json.dumps({"some": "stuff"}).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["error"]["code"], -32600)

    def _gen_rpc_req(self, method, params=None, request_id="2"):
        ret = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method
        }
        if params:
            ret["params"] = params
        return ret

    def test_missing_fields(self):
        req = self._gen_rpc_req("foo")
        del req["jsonrpc"]
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["error"]["code"], -32600)

        req = self._gen_rpc_req("foo")
        del req["id"]
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["error"]["code"], -32600)

        req = self._gen_rpc_req("foo")
        del req["method"]
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["error"]["code"], -32600)

    def test_invalid_method(self):
        req = self._gen_rpc_req("invalid", request_id="42")
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["id"], "42")
        self.assertEqual(res["error"]["code"], -32601)

    def test_getblockcount(self):
        # TODO: currently not returning a correct header height
        ndb = NotificationDB.instance()
        req = self._gen_rpc_req("getblockcount")
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertEqual(res["result"], 123)
