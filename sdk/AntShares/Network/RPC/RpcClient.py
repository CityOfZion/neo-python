# -*- coding:utf-8 -*-
"""
Description:
    RPC client
Usage:
    from AntShares.Network.RPC.RpcClient import RpcClient
"""
from random import randint
import requests
import json
import time


class RpcClient(object):
    """docstring for RpcClient"""
    def __init__(self, url="http://localhost:20332/"):
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

    def call(self, method, params):
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

