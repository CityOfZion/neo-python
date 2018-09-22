from neo.Core.Blockchain import Blockchain
from neo.api.JSONRPC.JsonRpcApi import JsonRpcApi, JsonRpcError
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neocore.UInt256 import UInt256
import datetime


class ExtendedJsonRpcApi:
    """
    Extended JSON-RPC API Methods
    """

    def get_node_state(self):
        height = Blockchain.Default().Height
        headers = Blockchain.Default().HeaderHeight
        diff = height - JsonRpcApi.start_height
        now = datetime.datetime.utcnow()
        difftime = now - JsonRpcApi.start_dt
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

    def get_tx_history(self):
        if JsonRpcApi.wallet:
            res = []
            for tx in JsonRpcApi.wallet.GetTransactions():
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
