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
from neo.Cryptography.Helper import *
from autologging import logged

@logged
class Contract(SerializableMixin, VerificationCode):
    """docstring for Contract"""

    PubKeyHash = None

    _address = None


    @property
    def Address(self):
        if self._address is None:
            self._address = Crypto.ToAddress(self.ScriptHash)
        return self._address

    @property
    def IsStandard(self):

        if len(self.Script) != 35:
            return False

        if self.Script[0] != 33 or self.Script[34] != CHECKSIG:
            return False

        return True




    def __init__(self, redeem_script=None, param_list=None, pubkey_hash=None):
        super(Contract, self).__init__()

        self.Script = redeem_script
        self.ParameterList = param_list
        self.PubKeyHash = pubkey_hash
        self._address = None

    @staticmethod
    def Create(publicKeyHash, parameterList, redeemScript):

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

        #for now we dont
        for key in keys:
            sb.push(key)

        sb.push(len(publicKeys))
        sb.add(CHECKMULTISIG)

        toarray = sb.ToArray()
#        tastr = toarray.decode('utf8')
        return toarray

    @staticmethod
    def CreateSignatureContract(publicKey):

        script = Contract.CreateSignatureRedeemScript(publicKey)
        params = [ContractParameterType.Signature]
        pubkey_hash = Crypto.ToScriptHash( publicKey.encode_point(True))

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


    def GetHashCode(self):
        if self.ScriptHash == None:
            self.ScriptHash = Contract.RedeemToScripthash(self.RedeemScript)
        return self.ScriptHash

    def ToScriptHash(self):
        return Crypto.Hash160(self.ScriptHash)

    def IsStandard(self):
        if len(self.RedeemScript) / 2 != 35:
            return False
        array = self.RedeemScript[:]
        if array[:2] != '21' or array[-2:] != 'ac':
            return False
        return True

    def Serialize(self, writer):
        writer.WriteBytes(self.ScriptHash)
        writer.WriteBytes(self.PubKeyHash)
        writer.WriteVarBytes(self.ParameterList)  # TODO need check
        writer.WriteVarBytes(self.RedeemScript)

    def Deserialize(self, reader):
        raise NotImplementedError()

    @staticmethod
    def PubkeyToRedeem(pubkey):
        return binascii.unhexlify('21'+ pubkey) + from_int_to_byte(int('ac',16))

    @staticmethod
    def RedeemToScripthash(redeem):
        return binascii.hexlify(bin_hash160(redeem))
