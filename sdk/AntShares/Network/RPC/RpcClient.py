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
        self.no = random.randint(1000)
        return str(self.no)

    def makeRequest(self, method, params):
        return {"method": method,
                "jsonrpc": "2.0",
                "id": self.get_id(),
                "params": params}

    def send(self, data):
        try:
            res = requests.post(self.url,
                                data=json.dumps(data),
                                headers=self.headers).json()
        except Exception as e:
            time.sleep(1)
            res = requests.post(self.url,
                                data=json.dumps(data),
                                headers=self.headers).json()
        return res
