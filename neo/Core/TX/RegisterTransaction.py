# -*- coding:utf-8 -*-
"""
Description:
    Register Transaction
Usage:
    from neo.Core.TX.RegisterTransaction import RegisterTransaction
"""
from neo.Core.TX.Transaction import Transaction, TransactionType
from neo.Core.AssetType import AssetType
from neocore.Cryptography.Crypto import Crypto
from neocore.Cryptography.ECCurve import EllipticCurve, ECDSA
from neo.Settings import settings
from neocore.Fixed8 import Fixed8


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

    def __init__(self, inputs=None,
                 outputs=None,
                 assettype=AssetType.GoverningToken,
                 assetname='',
                 amount=Fixed8(0),
                 precision=0,
                 owner=None,
                 admin=None):
        """
        Create an instance.

        Args:
            inputs (list):
            outputs (list):
            assettype (neo.Core.AssetType):
            assetname (str):
            amount (Fixed8):
            precision (int): number of decimals the asset has.
            owner (EllipticCurve.ECPoint):
            admin (UInt160):
        """
        super(RegisterTransaction, self).__init__(inputs, outputs)
        self.Type = TransactionType.RegisterTransaction  # 0x40
        self.AssetType = assettype
        self.Name = assetname
        self.Amount = amount  # Unlimited Mode: -0.00000001

        if inputs is not None:
            self.inputs = inputs
        else:
            self.inputs = []

        if outputs is not None:
            self.outputs = outputs
        else:
            self.outputs = []

        if owner is not None and type(owner) is not EllipticCurve.ECPoint:
            raise Exception("Invalid owner, must be ECPoint instance")

        self.Owner = owner
        self.Admin = admin
        self.Precision = precision

    def SystemFee(self):
        """
        Get the system fee.

        Returns:
            Fixed8:
        """
        if self.AssetType == AssetType.GoverningToken or self.AssetType == AssetType.UtilityToken:
            return Fixed8.Zero()

        return Fixed8(int(settings.REGISTER_TX_FEE))

    def GetScriptHashesForVerifying(self):
        """Get ScriptHash From SignatureContract"""
        # hashes = {}
        # super(RegisterTransaction, self).getScriptHashesForVerifying()
        pass

    def DeserializeExclusiveData(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neo.IO.BinaryReader):
        """
        self.Type = TransactionType.RegisterTransaction
        self.AssetType = reader.ReadByte()
        self.Name = reader.ReadVarString()
        self.Amount = reader.ReadFixed8()
        self.Precision = reader.ReadByte()
        self.Owner = ECDSA.Deserialize_Secp256r1(reader)
        #        self.Owner = ecdsa.G
        self.Admin = reader.ReadUInt160()

    def SerializeExclusiveData(self, writer):
        """
        Serialize object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        writer.WriteByte(self.AssetType)
        writer.WriteVarString(self.Name)
        writer.WriteFixed8(self.Amount)
        writer.WriteByte(self.Precision)

        self.Owner.Serialize(writer)

        writer.WriteUInt160(self.Admin)

    def ToJson(self):
        """
        Convert object members to a dictionary that can be parsed as JSON.

        Returns:
             dict:
        """
        jsn = super(RegisterTransaction, self).ToJson()

        asset = {
            'type': self.AssetType,
            'name': self.Name.decode('utf-8'),
            'amount': self.Amount.value,
            'precision': self.Precision if type(self.Precision) is int else self.Precision.decode('utf-8'),
            'owner': self.Owner.ToString(),
            'admin': Crypto.ToAddress(self.Admin)
        }
        jsn['asset'] = asset

        return jsn
