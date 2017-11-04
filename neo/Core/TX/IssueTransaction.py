# -*- coding:utf-8 -*-
"""
Description:
    Issue Transaction
Usage:
    from neo.Core.TX.IssueTransaction import IssueTransaction
"""
from neo.Core.TX.Transaction import Transaction, TransactionType

import random
from neo.Settings import settings
from neo.Fixed8 import Fixed8


class IssueTransaction(Transaction):

    Nonce = None

    """docstring for IssueTransaction"""

    def __init__(self, *args, **kwargs):
        super(IssueTransaction, self).__init__(*args, **kwargs)
        self.Type = TransactionType.IssueTransaction  # 0x40

    def SystemFee(self):
        return Fixed8(int(settings.ISSUE_TX_FEE))

    def GetScriptHashesForVerifying(self):
        pass

    def DeserializeExclusiveData(self, reader):
        self.Type = TransactionType.IssueTransaction
        pass

    def SerializeExclusiveData(self, writer):
        pass
