import json
from neo.api.JSONRPC.test_extended_json_rpc_api import ExtendedJsonRpcApiTestCase, mock_request


class NodeStatePluginTest(ExtendedJsonRpcApiTestCase):

    def test_get_node_state(self):
        req = self._gen_rpc_req("getnodestate")
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        self.assertGreater(res['result']['Progress'][0], 0)
        self.assertGreater(res['result']['Progress'][2], 0)
        self.assertGreater(res['result']['Time elapsed (minutes)'], 0)
