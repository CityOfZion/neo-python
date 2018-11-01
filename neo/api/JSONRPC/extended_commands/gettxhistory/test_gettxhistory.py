import json
import shutil
import os
from neo.Wallets.utils import to_aes_key
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.api.JSONRPC.test_extended_json_rpc_api import ExtendedJsonRpcApiTestCase, mock_request
from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase


class TxHistoryPluginTest(ExtendedJsonRpcApiTestCase):

    def test_gettxhistory_no_wallet(self):
        req = self._gen_rpc_req("gettxhistory")
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        error = res.get('error', {})
        self.assertEqual(error.get('code', None), -400)
        self.assertEqual(error.get('message', None), "Access denied.")

    def test_gettxhistory(self):
        test_wallet_path = shutil.copyfile(
            WalletFixtureTestCase.wallet_1_path(),
            WalletFixtureTestCase.wallet_1_dest()
        )
        self.app.wallet = UserWallet.Open(
            test_wallet_path,
            to_aes_key(WalletFixtureTestCase.wallet_1_pass())
        )
        req = self._gen_rpc_req("gettxhistory")
        mock_req = mock_request(json.dumps(req).encode("utf-8"))
        res = json.loads(self.app.home(mock_req))
        for tx in res['result']:
            self.assertIn('txid', tx.keys())
            self.assertIsNotNone(tx['txid'])
            self.assertIn('block_index', tx.keys())
            self.assertIsNotNone(tx['block_index'])
            self.assertIn('blocktime', tx.keys())
            self.assertIsNotNone(tx['blocktime'])
        self.assertEqual(len(res['result']), 9)
        self.app.wallet.Close()
        self.app.wallet = None
        os.remove(WalletFixtureTestCase.wallet_1_dest())
