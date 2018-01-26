from neo.SmartContract.ContractParameterType import ContractParameterType,ToName
from neo.VM.InteropService import StackItem,Array,ByteArray,Struct,Boolean,Integer,InteropInterface
import binascii
from neocore.UInt160 import UInt160
from neocore.UInt256 import UInt256
from neocore.Cryptography.ECCurve import ECDSA

class ContractParameter():

    Type = None
    Value = None

    def __init__(self, type, value):
        self.Type = type
        self.Value = value


    @staticmethod
    def Parse0x(param):
        if param[0:2] == '0x':
            return param[2:]
        return param

    @staticmethod
    def ParamToUInt160(param):
        shash_reversed = bytearray(binascii.unhexlify(ContractParameter.Parse0x(param)))
        shash_reversed.reverse()
        return UInt160(data=shash_reversed)

    @staticmethod
    def ParamToUInt256(param):
        shash_reversed = bytearray(binascii.unhexlify(ContractParameter.Parse0x(param)))
        shash_reversed.reverse()
        return UInt256(data=shash_reversed)

    @staticmethod
    def ToParameter(item:StackItem):

        if isinstance(item, Array) or isinstance(item, Struct):
            items = item.GetArray()
            output = [ContractParameter.ToParameter(subitem) for subitem in items]
            return ContractParameter(type=ContractParameterType.Array, value=output)

        elif isinstance(item, Boolean):
            return ContractParameter(type=ContractParameterType.Boolean, value=item.GetBoolean())

        elif isinstance(item, ByteArray):
            return ContractParameter(type=ContractParameterType.ByteArray, value=item.GetByteArray())

        elif isinstance(item, Integer):
            return ContractParameter(type=ContractParameterType.Integer, value=item.GetBigInteger())

        elif isinstance(item, InteropInterface):
            return ContractParameter(type=ContractParameterType.InteropInterface, value=item.GetInterface())


    def ToJson(self):
        jsn = {}
        jsn['type'] = str(ContractParameterType(self.Type))

        if self.Type in [ContractParameterType.Signature, ContractParameterType.ByteArray]:
            jsn['value'] = self.Value.hex()

        elif self.Type == ContractParameterType.Boolean:
            jsn['value'] = self.Value

        elif self.Type == ContractParameterType.String:
            jsn['value'] = str(self.Value)

        elif self.Type == ContractParameterType.Integer:
            jsn['value'] = self.Value

        # @TODO, see ``FromJson``, not sure if this is working properly
        elif self.Type == ContractParameterType.PublicKey:
            jsn['value'] = self.Value.ToString()

        elif self.Type in [ContractParameterType.Hash160,
                           ContractParameterType.Hash256]:
            jsn['value'] = self.Value.ToString()

        elif self.Type == ContractParameterType.Array:

            res = []
            for item in self.Value:
                res.append(item.ToJson())
            jsn['value'] = res

        return jsn

    @staticmethod
    def FromJson(json):
        type = ContractParameterType.FromString(json['type'])

        value = json['value']
        param = ContractParameter(type=type, value=None)

        if type == ContractParameterType.Signature or type == ContractParameterType.ByteArray:
            param.Value = bytearray.fromhex(value)

        elif type == ContractParameterType.Boolean:
            param.Value = bool(value)

        elif type == ContractParameterType.Integer:
            param.Value = int(value)

        elif type == ContractParameterType.Hash160:
            param.Value = ContractParameter.ParamToUInt160(value)

        elif type == ContractParameterType.Hash256:
            param.Value = ContractParameter.ParamToUInt256(value)

        # @TODO Not sure if this is working...
        elif type == ContractParameterType.PublicKey:
            param.Value = ECDSA.decode_secp256r1(value).G

        elif type == ContractParameterType.String:
            param.Value = str(value)

        elif type == ContractParameterType.Array:
            val = [ContractParameter.FromJson(item) for item in value]
            param.Value = val

        return param