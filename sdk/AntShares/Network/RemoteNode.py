# -*- coding:utf-8 -*-
"""
Description:
    Remote Node, use to broadcast tx
Usage:
    from AntShares.Network.RemoteNode import RemoteNode
"""
from AntShares.Network.RPC.RpcClient import RpcClient


class RemoteNode(object):
    """docstring for RemoteNode"""
    def __init__(self, url="http://localhost:20332/"):
        super(RemoteNode, self).__init__()
        self.rpc = RpcClient(url)

    def relay(tx):
        """tx: hex"""
        self.rpc.call(method="sendrawtransaction",
                      params=[tx])
