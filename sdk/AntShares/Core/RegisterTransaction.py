# -*- coding:utf-8 -*-
"""
Description:
    Register Transaction
Usage:
    from AntShares.Core.RegisterTransaction import RegisterTransaction
"""
from AntShares.Core.AssetType import AssetType
from AntShares.Helper import *
from AntShares.Fixed8 import Fixed8
from AntShares.Core.Transaction import Transaction
from AntShares.Core.TransactionType import TransactionType
from AntShares.Cryptography.Helper import *

import binascii


class RegisterTransaction(Transaction):
    """docstring for RegisterTransaction"""
    def __init__(self, inputs, outputs, assettype, assetname, amount, issuer, admin):
        super(RegisterTransaction, self).__init__(inputs, outputs)
        self.TransactionType = TransactionType.RegisterTransaction  # 0x40

        self.AssetType = assettype
        self.Name = binascii.hexlify("[{'lang':'zh-CN','name':'%s'}]" % str(assetname))

        # 发行总量，共有2种模式：
        # 1. 限量模式：当Amount为正数时，表示当前资产的最大总量为Amount，且不可修改（股权在未来可能会支持扩股或增发，会考虑需要公司签名或一定比例的股东签名认可）。
        # 2. 不限量模式：当Amount等于-1时，表示当前资产可以由创建者无限量发行。这种模式的自由度最大，但是公信力最低，不建议使用。
        # 在使用过程中，根据资产类型的不同，能够使用的总量模式也不同，具体规则如下：
        # 1. 对于股权，只能使用限量模式；
        # 2. 对于货币，只能使用不限量模式；
        # 3. 对于点券，可以使用任意模式；

        self.Amount = Fixed8(amount)  # Unlimited Mode: -0.00000001
        self.Issuer = issuer
        self.Admin = admin

    def getSystemFee(self):
        return Fixed8(100)

    def getScriptHashesForVerifying(self):
        """Get ScriptHash From SignatureContract"""
        # hashes = {}
        # super(RegisterTransaction, self).getScriptHashesForVerifying()
        pass


    def serializeExclusiveData(self, writer):
        writer.writeByte(self.AssetType)
        writer.writeVarBytes(self.Name)
        writer.writeFixed8(self.Amount)
        writer.writeBytes(self.Issuer)
        writer.writeBytes(self.Admin)
