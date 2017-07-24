# -*- coding:utf-8 -*-
"""
Description:
    Register Transaction
Usage:
    from neo.Core.TX.RegisterTransaction import RegisterTransaction
"""
from neo.Fixed8 import Fixed8
from neo.Core.TX.Transaction import Transaction,TransactionType

import binascii
from neo.Core.AssetType import AssetType

class RegisterTransaction(Transaction):
    """
        # 发行总量，共有2种模式：
        # 1. 限量模式：当Amount为正数时，表示当前资产的最大总量为Amount，且不可修改（股权在未来可能会支持扩股或增发，会考虑需要公司签名或一定比例的股东签名认可）。
        # 2. 不限量模式：当Amount等于-1时，表示当前资产可以由创建者无限量发行。这种模式的自由度最大，但是公信力最低，不建议使用。
        # 在使用过程中，根据资产类型的不同，能够使用的总量模式也不同，具体规则如下：
        # 1. 对于股权，只能使用限量模式；
        # 2. 对于货币，只能使用不限量模式；
        # 3. 对于点券，可以使用任意模式；


In English:
         # Total number of releases, there are 2 modes:
         # 1. Limited amount: When Amount is positive, it means that the maximum amount of current assets is Amount and can not be modified (the equity may support the expansion or issuance in the future, will consider the need for company signature or a certain percentage of shareholder signature recognition ).
         # 2. Unlimited mode: When Amount is equal to -1, it means that the current asset can be issued by the creator unlimited. This mode of freedom is the largest, but the credibility of the lowest, not recommended.
         # In the use of the process, according to the different types of assets, can use the total amount of different models, the specific rules are as follows:
         # 1. For equity, use only limited models;
         # 2. For currencies, use only unlimited models;
         # 3. For point coupons, you can use any pattern;
"""

    def __init__(self, inputs=[], outputs=[], assettype=AssetType.AntShare, assetname='', amount=Fixed8(0), issuer=None, admin=None):
        super(RegisterTransaction, self).__init__(inputs, outputs)
        self.TransactionType = TransactionType.RegisterTransaction  # 0x40

        self.AssetType = assettype
        self.Name = assetname

        self.Amount = Fixed8(amount)  # Unlimited Mode: -0.00000001
        self.Issuer = issuer
        self.Admin = admin

    def getSystemFee(self):
        return Fixed8(100)

    def GetScriptHashesForVerifying(self):
        """Get ScriptHash From SignatureContract"""
        # hashes = {}
        # super(RegisterTransaction, self).getScriptHashesForVerifying()
        pass


    def SerializeExclusiveData(self, writer):
        writer.writeByte(self.AssetType)
        print("name is: %s " % self.Name)
        writer.writeVarString(self.Name)
        writer.writeFixed8(self.Amount)
        writer.writeBytes(self.Issuer)
        writer.writeBytes(self.Admin)
