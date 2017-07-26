# -*- coding:utf-8 -*-
"""
Description:
    Issue Transaction
Usage:
    from neo.Core.TX.IssueTransaction import IssueTransaction
"""
from neo.Core.TX.Transaction import Transaction,TransactionType

import random


class IssueTransaction(Transaction):

    Nonce = None

    """docstring for IssueTransaction"""
    def __init__(self, *args, **kwargs):
        super(IssueTransaction, self).__init__(*args, **kwargs)
        self.TransactionType = TransactionType.IssueTransaction  # 0x40
        self.Nonce = self.GenNonce()

    def GenNonce(self):
        return random.randint(268435456, 4294967295)

    def GetScriptHashesForVerifying(self):
        """Get ScriptHash From SignatureContract"""
        pass

    def DeserializeExclusiveData(self, reader):
        reader.ReadUInt32()

    def SerializeExclusiveData(self, writer):
        writer.WriteUInt32(self.Nonce)
