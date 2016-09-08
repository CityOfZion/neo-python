# -*- coding:utf-8 -*-
"""
Description:
    Contract class in AntShares.Wallets
    Base class of all contracts
Usage:
    from AntShares.Wallets.Contract import Contract
"""

from AntShares.Cryptography.Helper import *
from AntShares.IO.ISerializable import ISerializable
from AntShares.Wallets.ContractParameterType import ContractParameterType
from AntShares.Core.Scripts.ScriptBuilder import ScriptBuilder, ScriptOp


class Contract(ISerializable):
    """docstring for Contract"""
    def __init__(self):
        super(Contract, self).__init__()
        self.redeemScript = None  # Contract script
        self.parameterList = []  # Parameters list of Contract Type
        self.publicKeyHash = None
        self.scriptHash = None

    def create(self, publicKeyHash, parameterList, redeemScript):
        self.redeemScript = redeemScript
        self.parameterList = parameterList
        self.publicKeyHash = publicKeyHash
        self.scriptHash = self.redeem_to_scripthash(redeemScript)

    def createSignatureContract(self, publicKey):
        result = self.redeem_to_scripthash(self.pubkey_to_redeem(publicKey))
        return self.create(result, [ContractParameterType.Signature], self.createSignatureRedeemScript(publicKey))

    def createSignatureRedeemScript(self, publicKey):
        sb = ScriptBuilder()
        sb.push(publicKey)
        sb.add(ScriptOp.OP_CHECKSIG)
        return sb.toArray()

    def equals(self, other):
        if id(self) == id(other):
            return True
        if not isinstance(other, Contract):
            return False
        return self.scriptHash == other.scriptHash

    def getAddress(self):
        # TODO
        return Wallet.toAddress(self.scriptHash)

    def getHashCode(self):
        if self.scriptHash == None:
            self.scriptHash = self.redeem_to_scripthash(self.redeemScript)
        return scripthash

    def isStandard(self):
        if len(self.redeemScript) / 2 != 35:
            return False
        array = self.redeemScript[:]
        if array[:2] != '21' or array[-2:] != 'ac':
            return False
        return True

    def serialize(self, writer):
        writer.writeBytes(self.scriptHash)
        writer.writeBytes(self.publicKeyHash)
        writer.writeVarBytes(self.parameterList[0])  # TODO need check
        writer.writeVarBytes(self.redeemScript)

    def deserialize(self, reader):
        # TODO
        pass

    def pubkey_to_redeem(self, pubkey):
        return binascii.unhexlify('21'+ pubkey) + from_int_to_byte(int('ac',16))

    def redeem_to_scripthash(self, redeem):
        return binascii.hexlify(bin_hash160(redeem))
