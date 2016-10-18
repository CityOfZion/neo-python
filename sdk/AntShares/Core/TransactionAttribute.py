# -*- coding:utf-8 -*-
"""
Description:
    Transaction Attribute
Usage:
    from AntShares.Core.TransactionAttribute import TransactionAttribute
"""

from AntShares.Core.TransactionAttributeUsage import TransactionAttributeUsage
from AntShares.Helper import *
from AntShares.Fixed8 import Fixed8
from AntShares.Network.Inventory import Inventory

import binascii


class TransactionAttribute(Inventory):
    """docstring for TransactionAttribute"""
    def __init__(self, usage, data):
        super(TransactionAttribute, self).__init__()
        self.usage = usage
        self.data = data

    def deserialize(self, reader):
        pass

    def serialize(self, writer):
        writer.writeByte(self.usage)
        byteLength = len(self.data)
        if self.usage == TransactionAttributeUsage.Script:
            writer.writeVarInt(byteLength)
        elif self.usage == TransactionAttributeUsage.CertUrl or self.usage == TransactionAttributeUsage.DescriptionUrl:
            writer.writeVarInt(byteLength)
        elif self.usage == TransactionAttributeUsage.Description or self.usage >= TransactionAttributeUsage.Remark:
            writer.writeVarInt(byteLength)

        if self.usage == TransactionAttributeUsage.ECDH02 or self.usage == TransactionAttributeUsage.ECDH03:
            writer.writeBytes(binascii.hexlify(self.data[1:33]))
        else:
            writer.writeBytes(binascii.hexlify(self.data))
