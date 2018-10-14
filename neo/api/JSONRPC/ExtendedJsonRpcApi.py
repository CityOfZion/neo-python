from neo.Core.Blockchain import Blockchain
from neo.api.JSONRPC.JsonRpcApi import JsonRpcApi, JsonRpcError
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neocore.UInt256 import UInt256
import datetime
import base58
from neo.Settings import settings


class ExtendedJsonRpcApi(JsonRpcApi):
    """
    Extended JSON-RPC API Methods
    """

    def __init__(self, port, wallet=None):
        self.start_height = Blockchain.Default().Height
        self.start_dt = datetime.datetime.utcnow()
        super(ExtendedJsonRpcApi, self).__init__(port, wallet)

    def json_rpc_method_handler(self, method, params):

        if method == "getnodestate":
            height = Blockchain.Default().Height
            headers = Blockchain.Default().HeaderHeight
            diff = height - self.start_height
            now = datetime.datetime.utcnow()
            difftime = now - self.start_dt
            mins = difftime / datetime.timedelta(minutes=1)
            secs = mins * 60
            bpm = 0
            tps = 0

            if diff > 0 and mins > 0:
                bpm = diff / mins
                tps = Blockchain.Default().TXProcessed / secs

            return {
                'Progress': [height, "/", headers],
                'Block-cache length': Blockchain.Default().BlockCacheCount,
                'Blocks since program start': diff,
                'Time elapsed (minutes)': mins,
                'Blocks per min': bpm,
                'TPS': tps
            }

        elif method == "gettxhistory":
            if self.wallet:
                res = []
                for tx in self.wallet.GetTransactions():
                    json = tx.ToJson()
                    tx_id = UInt256.ParseString(json['txid'])
                    txx, height = Blockchain.Default().GetTransaction(tx_id)
                    header = Blockchain.Default().GetHeaderByHeight(height)
                    block_index = header.Index
                    json['block_index'] = block_index
                    block_timestamp = header.Timestamp
                    json['blocktime'] = block_timestamp
                    res.append(json)
                return res
            else:
                raise JsonRpcError(-400, "Access denied.")

        elif method == "dumpprivkey":
            if self.wallet:
                return self.dump_priv_key(params)
            else:
                raise JsonRpcError(-400, "Access denied.")

        return super(ExtendedJsonRpcApi, self).json_rpc_method_handler(method, params)

    def dump_priv_key(self, params):
        if not params or params[0] == '':
            raise JsonRpcError(-100, "Missing argument")

        isValid = False
        try:
            data = base58.b58decode_check(params[0])
            if len(data) == 21 and data[0] == settings.ADDRESS_VERSION:
                isValid = True
        except Exception as e:
            pass
        if isValid:
            keys = self.wallet.GetKeys()
            for key in keys:
                if key.GetAddress() == params[0]:
                    export = key.Export()
                    return export
        raise JsonRpcError(-32602, "Invalid params")
