"""
Description:
    Contract Parameter Type in neo.Wallets
Usage:
    from neo.SmartContract.ContractParameterType import ContractParameterType
"""
from enum import Enum
import binascii


class ContractParameterType(Enum):
    """
    Contract Parameter Types are used to denote different types of objects used in the VM

    Attributes:
        Signature: 00
        Boolean: 01
        Integer: 02
        Hash160: 03
        Hash256: 04
        ByteArray: 05
        PublicKey: 06
        String: 07
        Array: 10
        InteropInterface: f0
        Void: ff
    """

    Signature = 0x00
    Boolean = 0x01
    Integer = 0x02
    Hash160 = 0x03
    Hash256 = 0x04
    ByteArray = 0x05
    PublicKey = 0x06
    String = 0x07
    Array = 0x10
    InteropInterface = 0xf0
    Void = 0xff

    def __str__(self):
        return self.name

    @staticmethod
    def FromString(val):
        """
        Create a ContractParameterType object from a str

        Args:
            val (str): the value to be converted to a ContractParameterType.
            val can be hex encoded (b'07'), int (7), string int ("7"), or string literal ("String")

        Returns:
            ContractParameterType
        """
        # first, check if the value supplied is the string literal of the enum (e.g. "String")

        if isinstance(val, bytes):
            val = val.decode('utf-8')

        try:
            return ContractParameterType[val]
        except Exception as e:
            # ignore a KeyError if the val isn't found in the Enum
            pass

        # second, check if the value supplied is bytes or hex-encoded (e.g. b'07')
        try:
            if isinstance(val, (bytearray, bytes)):
                int_val = int.from_bytes(val, 'little')
            else:
                int_val = int.from_bytes(binascii.unhexlify(val), 'little')
        except (binascii.Error, TypeError) as e:
            # if it's not hex-encoded, then convert as int (e.g. "7" or 7)
            int_val = int(val)

        return ContractParameterType(int_val)


import inspect


def ToName(param_type):
    """
    Gets the name of a ContractParameterType based on its value
    Args:
        param_type (ContractParameterType): type to get the name of

    Returns:
        str
    """
    items = inspect.getmembers(ContractParameterType)

    if type(param_type) is bytes:
        param_type = int.from_bytes(param_type, 'little')

    for item in items:
        name = item[0]
        val = int(item[1].value)

        if val == param_type:
            return name

    return None
