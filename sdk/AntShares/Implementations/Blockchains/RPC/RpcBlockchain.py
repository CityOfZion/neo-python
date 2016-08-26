# -*- coding:utf-8 -*-
"""
Description:
    RpcBlockchain Methods
Usage:
    from AntShares.Implementations.Blockchain.RPC.RpcBlockchain import RpcBlockchain
"""


from AntShares.Network.RPC.RpcClient import RpcClient


class RpcBlockchain(object):
    """docstring for RpcBlockchain"""
    def __init__(self, url="http://localhost:20332/"):
        super(RpcBlockchain, self).__init__()
        self.rpc = RpcClient(url)
