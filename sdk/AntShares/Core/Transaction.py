# -*- coding:utf-8 -*-
"""
Description:
    Transaction Basic Class
Usage:
    from AntShares.Core.Transaction import Transaction
"""

from AntShares.Core.AssetType import AssetType
from AntShares.Core.TransactionType import TransactionType
from AntShares.Helper import *
from AntShares.Fixed8 import Fixed8


class Transaction(object):
    """docstring for Transaction"""
    def __init__(self, inputs, outputs):
        super(Transaction, self).__init__()
        self.inputs = inputs
        self.outputs = outputs
        self.attributes = []
        self.scripts = []
        self.TransactionType = TransactionType.ContractTransaction
        self.InventoryType = 0x01  # InventoryType TX 0x01
        self.systemFee = self.getSystemFee()

    def getAllInputs(self):
        return self.inputs

    def getReference(self):
        inputs = self.getAllInputs()

        # TODO
        # Blockchain.getTransaction
        txs = [Blockchain.getTransaction(_input.prevHash) for _input in inputs]
        if inputs == []:
            raise Exception, 'No Inputs.'
        else:
            res = {}
            for _input in inputs:
                i = inputs.index(_input)
                res.update({_input.toString(): txs[i].outputs[_input.prevIndex]})

            return res

    def getSystemFee(self):
        if self.TransactionType == TransactionType.RegisterTransaction:  # 0x40
            return Fixed8(100)
        else:
            return Fixed8(0)

    def getScriptHashesForVerifying(self):
        """Get ScriptHash From SignatureContract"""
        hashes = {}
        result = self.getReference()

        if result == None:
            raise Exception, 'getReference None.'

        for _input in self.inputs:
            _hash = result.get(_input.toString()).scriptHash
            hashes.update({_hash.toString(), _hash})

        # TODO
        # Blockchain.getTransaction
        txs = [Blockchain.getTransaction(output.AssetId) for output in self.outputs]
        for output in self.outputs:
            tx = txs[self.outputs.index(output)]
            if tx == None:
                raise Exception, "Tx == None"
            else:
                if tx.AssetType & AssetType.DutyFlag:
                    hashes.update(output.ScriptHash.toString(), output.ScriptHash)

                    array = sorted(hashes.keys())
                    return array

    def serialize(self, writer):
        self.serializeUnsigned(writer)
        writer.writeSerializableArray(self.scripts)

    def serializeUnsigned(self, writer):
        writer.writeByte(self.TransactionType)
        self.serializeExclusiveData(writer)
        writer.writeSerializableArray(self.attributes)
        writer.writeSerializableArray(self.inputs)
        writer.writeSerializableArray(self.outputs)

    def serializeExclusiveData(self, writer):
        pass
