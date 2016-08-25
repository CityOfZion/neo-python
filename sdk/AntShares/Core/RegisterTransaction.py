# -*- coding:utf-8 -*-
"""
Description:
    Register Transaction
Usage:
    from AntShares.Core.RegisterTransaction import RegisterTransaction
"""
from AntShares.Core.AssetType import AssetType
from AntShares.Core.Helper import *
from AntShares.Core.Transaction import Transaction
from bitcoin import *
import binascii


class RegisterTransaction(Transaction):
    """docstring for RegisterTransaction"""
    def __init__(self, assetname, amount, issuer, admin):
        super(RegisterTransaction, self).__init__([], [])
        self.AssetType = AssetType.RegisterTransaction  # 0x40

        self.Name = "[{'lang':'zh-CN','name':'%s'}]" % assetname

        # 发行总量，共有2种模式：
        # 1. 限量模式：当Amount为正数时，表示当前资产的最大总量为Amount，且不可修改（股权在未来可能会支持扩股或增发，会考虑需要公司签名或一定比例的股东签名认可）。
        # 2. 不限量模式：当Amount等于-1时，表示当前资产可以由创建者无限量发行。这种模式的自由度最大，但是公信力最低，不建议使用。
        # 在使用过程中，根据资产类型的不同，能够使用的总量模式也不同，具体规则如下：
        # 1. 对于股权，只能使用限量模式；
        # 2. 对于货币，只能使用不限量模式；
        # 3. 对于点券，可以使用任意模式；

        self.Amount = float_2_hex(amount)  # Unlimited Mode: -0.00000001
        self.Issuer = issuer
        self.Admin = admin


    def getScriptHashesForVerifying(self):
        """Get ScriptHash From SignatureContract"""
        pass

    #
    # def deserializeExclusiveData(self):
    #     pass
