from neo.api.JSONRPC.ExtendedRpcCommand import ExtendedRpcCommand
from neo.Core.Blockchain import Blockchain
import datetime
from neocore.UInt256 import UInt256
from neo.api.JSONRPC.JsonRpcApi import JsonRpcError


class TxHistoryCmd(ExtendedRpcCommand):
    start_height = Blockchain.Default().Height
    start_dt = datetime.datetime.utcnow()

    @classmethod
    def commands(cls):
        return ["gettxhistory"]

    @classmethod
    def execute(cls, json_rpc_api, method, params):
        if method == "gettxhistory":
            if json_rpc_api.wallet:
                res = []
                for tx in json_rpc_api.wallet.GetTransactions():
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
