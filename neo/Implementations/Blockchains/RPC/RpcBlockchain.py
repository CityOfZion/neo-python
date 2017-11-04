# -*- coding:utf-8 -*-
"""
Description:
    RpcBlockchain Methods
Usage:
    from neo.Implementations.Blockchain.RPC.RpcBlockchain import RpcBlockchain
"""


from neo.Network.RPC.RpcClient import RpcClient
from neo.Defaults import TEST_NODE


class RpcBlockchain(object):
    """docstring for RpcBlockchain"""

    def __init__(self, url=TEST_NODE):
        super(RpcBlockchain, self).__init__()
        self.rpc = RpcClient(url)
