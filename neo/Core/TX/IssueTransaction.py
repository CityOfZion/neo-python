# -*- coding:utf-8 -*-
"""
Description:
    Issue Transaction
Usage:
    from neo.Core.TX.IssueTransaction import IssueTransaction
"""
from neo.Core.TX.Transaction import Transaction, TransactionType
from neo.Settings import settings
from neocore.Fixed8 import Fixed8
from neo.Blockchain import GetSystemCoin, GetSystemShare


class IssueTransaction(Transaction):
    Nonce = None

    """docstring for IssueTransaction"""

    def __init__(self, *args, **kwargs):
        """
        Create an instance.

        Args:
            *args:
            **kwargs:
        """
        super(IssueTransaction, self).__init__(*args, **kwargs)
        self.Type = TransactionType.IssueTransaction  # 0x40

    def SystemFee(self):
        """
        Get the system fee.

        Returns:
            Fixed8:
        """
        if self.Version >= 1:
            return Fixed8.Zero()

        # if all outputs are NEO or gas, return 0
        all_neo_gas = True
        for output in self.outputs:
            if output.AssetId != GetSystemCoin().Hash and output.AssetId != GetSystemShare().Hash:
                all_neo_gas = False
        if all_neo_gas:
            return Fixed8.Zero()

        return Fixed8(int(settings.ISSUE_TX_FEE))

    def GetScriptHashesForVerifying(self):
        pass

    def DeserializeExclusiveData(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neo.IO.BinaryReader):
        """

        self.Type = TransactionType.IssueTransaction

        if self.Version > 1:
            raise Exception('Invalid TX Type')

    def SerializeExclusiveData(self, writer):
        pass
