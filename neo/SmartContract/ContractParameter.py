from neo.SmartContract.ContractParameterType import ContractParameterType
from neo.VM.InteropService import StackItem, Array, ByteArray, Struct, Boolean, Integer, InteropInterface
from neocore.UInt160 import UInt160
from neocore.UInt256 import UInt256
from neocore.BigInteger import BigInteger
from neocore.Cryptography.ECCurve import ECDSA
import binascii


class ContractParameter:
    """Contract Parameter used for parsing parameters sent to and from smart contract invocations"""

    Type = None
    Value = None

    def __init__(self, type, value):
        """

        Args:
            type (neo.SmartContract.ContractParameterType.ContractParameterType): The type of the parameter
            value (*): The value of the parameter
        """
        self.Type = type
        self.Value = value

    @staticmethod
    def ToParameter(item: StackItem):
        """
        Convert a StackItem to a ContractParameter object

        Args:
            item (neo.VM.InteropService.StackItem) The item to convert to a ContractParameter object

        Returns:
            ContractParameter

        """
        if isinstance(item, Array) or isinstance(item, Struct):
            items = item.GetArray()
            output = [ContractParameter.ToParameter(subitem) for subitem in items]
            return ContractParameter(type=ContractParameterType.Array, value=output)

        elif isinstance(item, Boolean):
            return ContractParameter(type=ContractParameterType.Boolean, value=item.GetBoolean())

        elif isinstance(item, ByteArray):
            return ContractParameter(type=ContractParameterType.ByteArray, value=item.GetByteArray())

        elif isinstance(item, Integer):
            return ContractParameter(type=ContractParameterType.Integer, value=str(item.GetBigInteger()))

        elif isinstance(item, InteropInterface):
            return ContractParameter(type=ContractParameterType.InteropInterface, value=item.GetInterface())

    @staticmethod
    def AsParameterType(type: ContractParameterType, item: StackItem):
        """
        Convert a StackItem to a ContractParameter object of a specified ContractParameterType
        Args:
            type (neo.SmartContract.ContractParameterType): The ContractParameterType to convert to
            item (neo.VM.InteropService.StackItem): The item to convert to a ContractParameter object

        Returns:

        """
        if type == ContractParameterType.Integer:
            return ContractParameter(type, value=item.GetBigInteger())
        elif type == ContractParameterType.Boolean:
            return ContractParameter(type, value=item.GetBoolean())
        elif type == ContractParameterType.Array:
            output = [ContractParameter.ToParameter(subitem) for subitem in item.GetArray()]
            return ContractParameter(type, value=output)
        elif type == ContractParameterType.String:
            return ContractParameter(type, value=item.GetString())
        elif type == ContractParameterType.InteropInterface:
            return ContractParameter(type, value=item.GetInterface())
        # all other types return a byte array
        else:
            return ContractParameter(type, value=item.GetByteArray())

    def ToJson(self, auto_hex=True):
        """
        Converts a ContractParameter instance to a json representation

        Returns:
            dict: a dictionary representation of the contract parameter
        """
        jsn = {}
        jsn['type'] = str(ContractParameterType(self.Type))

        if self.Type == ContractParameterType.Signature:
            jsn['value'] = self.Value.hex()

        elif self.Type == ContractParameterType.ByteArray:
            if auto_hex:
                jsn['value'] = self.Value.hex()
            else:
                jsn['value'] = self.Value
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
                if item:
                    res.append(item.ToJson(auto_hex=auto_hex))
            jsn['value'] = res

        elif self.Type == ContractParameterType.InteropInterface:
            try:
                jsn['value'] = self.Value.ToJson()
            except Exception as e:
                pass

        return jsn

    def ToVM(self):
        """
        Used for turning a ContractParameter item into somethnig consumable by the VM

        Returns:

        """
        if self.Type == ContractParameterType.String:
            return str(self.Value).encode('utf-8').hex()
        elif self.Type == ContractParameterType.Integer and isinstance(self.Value, int):
            return BigInteger(self.Value)
        return self.Value

    @staticmethod
    def FromJson(json):
        """
        Convert a json object to a ContractParameter object

        Args:
            item (dict): The item to convert to a ContractParameter object

        Returns:
            ContractParameter

        """
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
            param.Value = UInt160.ParseString(value)

        elif type == ContractParameterType.Hash256:
            param.Value = UInt256.ParseString(value)

        # @TODO Not sure if this is working...
        elif type == ContractParameterType.PublicKey:
            param.Value = ECDSA.decode_secp256r1(value).G

        elif type == ContractParameterType.String:
            param.Value = str(value)

        elif type == ContractParameterType.Array:
            val = [ContractParameter.FromJson(item) for item in value]
            param.Value = val

        return param
