# -*- coding:utf-8 -*-
"""
Description:
    Contract Parameter Type in neo.Wallets
Usage:
    from neo.SmartContract.ContractParameterType import ContractParameterType
"""
from enum import Enum
import binascii

class ContractParameterType(Enum):
    Signature = 0x00        # 签名
    Boolean = 0x01
    Integer = 0x02          # 整数
    Hash160 = 0x03          # 160位散列值
    Hash256 = 0x04          # 256位散列值
    ByteArray = 0x05        # 字节数组
    PublicKey = 0x06
    String = 0x07
    Array = 0x10
    InteropInterface = 0xf0
    Void = 0xff


    def __str__(self):
        return str(self.value.to_bytes(1,'little').hex())

    @staticmethod
    def FromString(val):
        return ContractParameterType(int.from_bytes( binascii.unhexlify(val), 'little'))

import inspect


def ToName(param_type):

    items = inspect.getmembers(ContractParameterType)

    if type(param_type) is bytes:
        param_type = int.from_bytes(param_type, 'little')

    for item in items:
        name = item[0]
        val = int(item[1])

        if val == param_type:
            return name

    return None
