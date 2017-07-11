# -*- coding:utf-8 -*-
"""
Description:
    Remote Node, use to broadcast tx
Usage:
    from neo.Network.RemoteNode import RemoteNode
"""


from neo.Network.RPC.RpcClient import RpcClient
from neo.Defaults import TEST_NODE

class RemoteNode(object):
    """docstring for RemoteNode"""
    def __init__(self, url=TEST_NODE):
        super(RemoteNode, self).__init__()
        self.rpc = RpcClient(url)

    def sendRawTransaction(self, tx):
        """
        Send Transaction
        """
        return self.rpc.call(method="sendrawtransaction",
                             params=[tx])

    def getBestBlockhash(self):
        """
        Get Best BlockHash from chain
        """
        return self.rpc.call(method="getbestblockhash",
                             params=[]).get("result", "")

    def getBlock(self, hint, verbose=1):
        """
        Get Block from chain with hash or index
        hint : blockhash or index
        Verbose: 0-Simple, 1-Verbose
        """
        if verbose not in (0, 1):
            raise ValueError('verbose, should be 0 or 1.')
        return self.rpc.call(method="getblock",params=[hint, verbose])

    def getBlockCount(self):
        """
        Get Block Count from chain
        """
        return self.rpc.call(method="getblockcount",
                             params=[]).get('result', 0)

    def getBlockHash(self, index):
        """
        Get BlockHash from chain by index
        """
        return self.rpc.call(method="getblockhash",
                             params=[index]).get('result', '')

    def getConnectionCount(self):
        """
        Get Connection Count from chain
        """
        return self.rpc.call(method="getconnectioncount",
                             params=[]).get('result', 0)

    def getRawMemPool(self):
        """
        Get Uncomfirmed tx in Memory Pool
        """
        return self.rpc.call(method="getrawmempool",
                             params=[])

    def getRawTransaction(self, txid, verbose=0):
        """
        Get comfirmed tx from chain
        Verbose: 0-Simple, 1-Verbose
        """
        if verbose not in (0, 1):
            raise ValueError('verbose, should be 0 or 1.')

        return self.rpc.call(method="getrawtransaction",
                             params=[txid, verbose])

    def getTxOut(self, txid, n=0):
        """
        Get Tx Output from chain
        """
        return self.rpc.call(method="gettxout",
                             params=[txid, n])
