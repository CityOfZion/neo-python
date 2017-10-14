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
    String = 0x07
    Array = 0x10
    Void = 0xff



import inspect
#import sys
#import importlib
import binascii

#module = importlib.import_module('neo.SmartContract.ContractParameterType')
#items = dir(sys.modules[__name__])


def ToName(param_type):

    items = inspect.getmembers(ContractParameterType)

    if type(param_type) is bytes:
        param_type = int.from_bytes(param_type, 'little')

    for item in items:
        name = item[0]
        val = int(item[1])
        print("name, val %s %s %s" % (name,val, param_type))

        if val == param_type:
            return name

    return None
