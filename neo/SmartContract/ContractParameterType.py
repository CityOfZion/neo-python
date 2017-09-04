# -*- coding:utf-8 -*-
"""
Description:
    Contract Parameter Type in neo.Wallets
Usage:
    from neo.SmartContract.ContractParameterType import ContractParameterType
"""


class ContractParameterType(object):
    Signature = 0x00        # 签名
    Boolean = 0x01
    Integer = 0x02          # 整数
    Hash160 = 0x03          # 160位散列值
    Hash256 = 0x04          # 256位散列值
    ByteArray = 0x05        # 字节数组
    PublicKey = 0x06
    Array = 16
    Void = 0xff
