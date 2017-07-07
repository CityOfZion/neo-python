# -*- coding:utf-8 -*-
"""
Description:
    Transaction Basic Class
Usage:
    from AntShares.Core.Transaction import Transaction
"""

from AntShares.Core.AssetType import AssetType
from AntShares.Core.Blockchain import Blockchain
from AntShares.Core.TransactionType import TransactionType
from AntShares.Fixed8 import Fixed8
from AntShares.Network.Inventory import Inventory
from AntShares.Network.Mixins import InventoryMixin
from AntShares.Cryptography.Crypto import *

class Transaction(Inventory, InventoryMixin):

    __hash = None

    Type = TransactionType.RegisterTransaction

    """docstring for Transaction"""
    def __init__(self, inputs, outputs, attributes = {}):
        super(Transaction, self).__init__()
        self.inputs = inputs
        self.outputs = outputs
        self.attributes = attributes
        self.scripts = []
        self.TransactionType = TransactionType.ContractTransaction
        self.InventoryType = 0x01  # InventoryType TX 0x01
        self.systemFee = self.getSystemFee()


    def Hash(self):
        if not self.__hash:
            self.__hash = Crypto.Hash256( self.GetHashData())
        return self.__hash


    def getAllInputs(self):
        return self.inputs

    def getReference(self):
        inputs = self.getAllInputs()

        # TODO
        # Blockchain.getTransaction
#        txs = [Blockchain.getTransaction(_input.prevHash) for _input in inputs]
#        if inputs == []:
#            raise Exception, 'No Inputs.'
#        else:
#            res = {}
#            for _input in inputs:
#                i = inputs.index(_input)
#                res.update({_input.toString(): txs[i].outputs[_input.prevIndex]})
#            return res
        return None

    def getSystemFee(self):
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
        # ReWrite in RegisterTransaction and IssueTransaction#
        pass


    def DeserializeExclusiveData(self, reader):
        pass

    def OnDeserialized(self):
        pass