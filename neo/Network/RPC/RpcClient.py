# -*- coding:utf-8 -*-
"""
Description:
    RPC client
Usage:
    from neo.Network.RPC.RpcClient import RpcClient
"""
from random import randint
import requests
import json
import time
from neo.Defaults import TEST_NODE


class RpcClient(object):
    """docstring for RpcClient"""
    def __init__(self, url=TEST_NODE):
        super(RpcClient, self).__init__()
        self.no = 0
        self.url = url
        self.headers = {'content-type': 'application/json'}

    def get_id(self):
        self.no = randint(0,1000)
        return str(self.no)

    def makeRequest(self, method, params):
        return {"method": method,
                "jsonrpc": "2.0",
                "id": self.get_id(),
                "params": params}

    def send(self, data):
        res = requests.post(self.url,
                            data=json.dumps(data),
                            headers=self.headers).json()
        return res

    def call(self, method, params=None):
        data = self.makeRequest(method, params)
        try:
            res = self.send(data)
            #print res
        except Exception as e:
            #print e
            time.sleep(1) # wait 1 seconds
            res = self.send(data)
        #print res
        return res

    def callBatch(self, requests):
        if not isinstance(requests, dict):
            return []
        requests = [self.makeRequest(request.get('method', ''),
                                     request.get('params', ''))
                    for request in requests]

        return [self.call(request) for request in requests]



    def sendRawTransaction(self, tx):
        """
        Send Transaction
        """
        return self.call(method="sendrawtransaction",
                             params=[tx])

    def getBestBlockhash(self):
        """
        Get Best BlockHash from chain
        """
        return self.call(method="getbestblockhash",
                             params=[]).get("result", "")

    def getBlock(self, hint, verbose=1):
        """
        Get Block from chain with hash or index
        hint : blockhash or index
        Verbose: 0-Simple, 1-Verbose
        """
        if verbose not in (0, 1):
            raise ValueError('verbose, should be 0 or 1.')
        return self.call(method="getblock",params=[hint, verbose])

    def getBlockCount(self):
        """
        Get Block Count from chain
        """
        return self.call(method="getblockcount",
                             params=[]).get('result', 0)

    def getBlockHash(self, index):
        """
        Get BlockHash from chain by index
        """
        return self.call(method="getblockhash",
                             params=[index]).get('result', '')

    def getConnectionCount(self):
        """
        Get Connection Count from chain
        """
        return self.call(method="getconnectioncount",
                             params=[]).get('result', 0)

    def getRawMemPool(self):
        """
        Get Uncomfirmed tx in Memory Pool
        """
        return self.call(method="getrawmempool",
                             params=[])

    def getRawTransaction(self, txid, verbose=0):
        """
        Get comfirmed tx from chain
        Verbose: 0-Simple, 1-Verbose
        """
        if verbose not in (0, 1):
            raise ValueError('verbose, should be 0 or 1.')

        return self.call(method="getrawtransaction",
                             params=[txid, verbose])

    def getTxOut(self, txid, n=0):
        """
        Get Tx Output from chain
        """
        return self.call(method="gettxout",
                             params=[txid, n])
