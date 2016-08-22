# -*- coding:utf-8 -*-
"""
Description:
    Transaction Basic Class
Usage:
    from AntShares.Core.Transaction import Transaction
"""

from AntShares.Core.AssetType import AssetType
from AntShares.Core.Helper import *


class Transaction(object):
    """docstring for Transaction"""
    def __init__(self, inputs, outputs):
        super(Transaction, self).__init__()
        self.inputs = inputs
        self.outputs = outputs
        self.attributes = []
        self.scripts = []
        self.AssetType = None
        self.InventoryType = 0x01  # InventoryType TX 0x01
        self.systemFee = self.getSystemFee()

    def getAllInputs(self):
        return self.inputs

    def getReference(self):
        inputs = self.getAllInputs()
        # TODO

    def getSystemFee(self):
        if self.AssetType == AssetType.RegisterTransaction:  # 0x40
            return 100
        else:
            return 0

    def serialize(self, writer):
        self.serializeUnsigned(writer)
        writer.writeSerializableArray(self.scripts)

    def serializeUnsigned(self, writer):
        self.writer.writeByte(self.AssetType)
        self.serializeExclusiveData(writer)
        self.writer.writeSerializableArray(self.attributes)
        self.writer.writeSerializableArray(self.inputs)
        self.writer.writeSerializableArray(self.outputs)

    def serializeExclusiveData(self, writer):
        pass
