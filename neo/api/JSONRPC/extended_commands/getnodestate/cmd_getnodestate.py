from neo.api.JSONRPC.ExtendedRpcCommand import ExtendedRpcCommand
from neo.Core.Blockchain import Blockchain
import datetime


class NodeStateCmd(ExtendedRpcCommand):

    @classmethod
    def commands(cls):
        return ["getnodestate"]

    @classmethod
    def execute(cls, json_rpc_api, method, params):
        if method == "getnodestate":
            height = Blockchain.Default().Height
            headers = Blockchain.Default().HeaderHeight
            diff = height - json_rpc_api.start_height
            now = datetime.datetime.utcnow()
            difftime = now - json_rpc_api.start_dt
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
