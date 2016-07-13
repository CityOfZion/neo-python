# -*- coding:utf-8 -*-
"""
Description:
    Contract Parameter Type in AntShares.Wallets
Usage:
    from AntShares.Wallets.ContractParameterType import ContractParameterType
"""


class ContractParameterType(object):
    Signature = 0x00        # 签名
    Integer = 0x01          # 整数
    Hash160 = 0x02          # 160位散列值
    Hash256 = 0x03          # 256位散列值
    ByteArray = 0x04        # 字节数组
