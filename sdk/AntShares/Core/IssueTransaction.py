# -*- coding:utf-8 -*-
"""
Description:
    Issue Transaction
Usage:
    from AntShares.Core.IssueTransaction import IssueTransaction
"""
from AntShares.Core.AssetType import AssetType
from AntShares.Helper import *
from AntShares.Fixed8 import Fixed8
from AntShares.Core.Transaction import Transaction
from AntShares.Core.TransactionType import TransactionType
from AntShares.Cryptography.Helper import *

import binascii
from random import randint


class IssueTransaction(Transaction):
    """docstring for IssueTransaction"""
    def __init__(self, inputs, outputs):
        super(IssueTransaction, self).__init__(inputs, outputs)
        self.TransactionType = TransactionType.IssueTransaction  # 0x40

        self.Nonce = self.genNonce()

    def genNonce(self):
        return random.randint(268435456, 4294967295)

    def getScriptHashesForVerifying(self):
        """Get ScriptHash From SignatureContract"""
        pass

    def serializeExclusiveData(self, writer):
        writer.writeUInt32(self.Nonce)
