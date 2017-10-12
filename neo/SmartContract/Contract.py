# -*- coding:utf-8 -*-
"""
Description:
    Contract class in neo.Wallets
    Base class of all contracts
Usage:
    from neo.SmartContract.Contract import Contract
"""
from io import BytesIO,BufferedReader,BufferedWriter
from neo.VM.OpCode import *
from neo.VM.ScriptBuilder import ScriptBuilder
from neo.Cryptography.Crypto import *
from neo.IO.Mixins import SerializableMixin
from neo.SmartContract.ContractParameterType import ContractParameterType
from neo.Core.VerificationCode import VerificationCode
from neo.Core.Helper import Helper
from neo.Cryptography.Helper import *
from autologging import logged


class ContractType():
    SignatureContract = 0
    MultiSigContract = 1
    CustomContract = 2

@logged
class Contract(SerializableMixin, VerificationCode):
    """docstring for Contract"""

    PublicKeyHash = None

    _address = None


    @property
    def Address(self):
        if self._address is None:
            self._address = Crypto.ToAddress(self.ScriptHash)
        return self._address

    @property
    def IsStandard(self):
        scp = binascii.unhexlify(self.Script)

        if len(scp) != 35:
            return False

        if scp[0] != 33 or scp[34] != int.from_bytes(CHECKSIG, 'little'):
            return False

        return True

    @property
    def Type(self):
        if self.IsStandard:
            return ContractType.SignatureContract
        elif self.IsMultiSigContract():
            return ContractType.MultiSigContract
        return ContractType.CustomContract


    def __init__(self, redeem_script=None, param_list=None, pubkey_hash=None):
        super(Contract, self).__init__()

        self.Script = redeem_script
        self.ParameterList = param_list
        self.PublicKeyHash = pubkey_hash
        self._address = None

    @staticmethod
    def Create(redeemScript, parameterList, publicKeyHash):

        return Contract(redeemScript, parameterList, publicKeyHash)



    @staticmethod
    def CreateMultiSigContract(publickKeyHash, m, publicKeys):
        raise NotImplementedError()

    @staticmethod
    def CreateMultiSigRedeemScript(m, publicKeys):

        if m < 2 or m > len(publicKeys) or len(publicKeys) > 1024:
            raise Exception('Invalid keys')

        sb = ScriptBuilder()
        sb.push(m)

        pkeys = [point for point in publicKeys]
        pkeys.sort()
        keys = [p.encode_point().decode() for p in pkeys]

        for key in keys:
            sb.push(key)

        sb.push(len(publicKeys))
        sb.add(CHECKMULTISIG)

        return sb.ToArray()

    @staticmethod
    def CreateSignatureContract(publicKey):

        script = Contract.CreateSignatureRedeemScript(publicKey)
        params = bytearray([ContractParameterType.Signature])
        encoded = publicKey.encode_point(True)
        pubkey_hash = Crypto.ToScriptHash( encoded, unhex=True)

        return Contract(script, params, pubkey_hash)


    @staticmethod
    def CreateSignatureRedeemScript(publicKey):
        sb = ScriptBuilder()
        sb.push(publicKey.encode_point(compressed=True))
        sb.add(CHECKSIG)
        return sb.ToArray()

    def Equals(self, other):
        if id(self) == id(other):
            return True
        if not isinstance(other, Contract):
            return False
        return self.ScriptHash == other.ScriptHash



    def ToScriptHash(self):
        return Crypto.Hash160(self.ScriptHash)


    def Deserialize(self, reader):
        self.PublicKeyHash = reader.ReadUInt160()

        self.ParameterList = reader.ReadVarBytes()
        script = bytearray(reader.ReadVarBytes()).hex()
        self.Script = script.encode('utf-8')


    def Serialize(self, writer):
        writer.WriteUInt160(self.PublicKeyHash)
        writer.WriteVarBytes(self.ParameterList)
        writer.WriteVarBytes(self.Script)

    def IsMultiSigContract(self):
        #Not implemented
        return False


    @staticmethod
    def PubkeyToRedeem(pubkey):
        return binascii.unhexlify('21'+ pubkey) + from_int_to_byte(int('ac',16))

    @staticmethod
    def RedeemToScripthash(redeem):
        return binascii.hexlify(bin_hash160(redeem))


    def ToArray(self):
        return Helper.ToArray(self)

    def ToJson(self):
        jsn = {}
        jsn['PublicKeyHash'] = self.PublicKeyHash.ToString()
        jsn['Parameters'] = bytes(self.ParameterList).decode('utf-8')
        jsn['Script'] = self.Script.decode('utf-8')
        return jsn
