from neo.SmartContract.Contract import Contract,ContractType
from neo.SmartContract.ContractParameterType import ContractParameterType
from neo.VM.ScriptBuilder import ScriptBuilder
from neo.VM import OpCode
from neo.Core.Witness import Witness
import json
import binascii

class ContractParametersContext():


    Verifiable = None

    ScriptHashes = None
    Verifications = None
    Parameters = None

    def __init__(self, verifiable):

        self.Verifiable = verifiable
        self.ScriptHashes = verifiable.GetScriptHashesForVerifying()
        self.Verifications = [None] * len(self.ScriptHashes)
        self.Parameters = [None] * len(self.ScriptHashes)

    @property
    def Completed(self):
        for p in self.Parameters:
            if p is None:
                return False
            for p2 in p:
                if p2 is None:
                    return False
        return True


    def Add(self, contract, index, parameter):

        i = self.GetIndex(contract.ScriptHash)

        if i < 0:
            return False

        if self.Verifications[i] is None:
            self.Verifications[i] = contract.Script

        if self.Parameters[i] is None:
            self.Parameters[i] = [None] * len(contract.ParameterList)
            self.Parameters[i][index] = binascii.hexlify( parameter )

        return True


    def AddSignature(self, contract, pubkey, signature):

        if contract.Type == ContractType.MultiSigContract:

            raise NotImplementedError('Multi sig contracts not yet implemented')


        else:

            index = -1
            for i, contractParam in enumerate(contract.ParameterList):
                if contractParam == ContractParameterType.Signature:
                    if index >=0:
                        raise Exception("Signature must be first")
                    else:
                        index = i

            return self.Add(contract, index, signature)

    def GetIndex(self, script_hash):
        for index, hash in enumerate(self.ScriptHashes):
            if hash == script_hash:
                return index
        return -1

    def GetParameter(self, scriptHash, index):
        return self.Parameters[self.GetIndex(scriptHash)][index]


    def GetScripts(self):

        if not self.Completed:
            raise Exception("Signature Context not complete")

        scripts = []

        for i in range(0, len(self.Parameters)):

            sb = ScriptBuilder()

            plist = list(self.Parameters[i])
            plist.reverse()

            for p in plist:
                sb.push(p)

            witness = Witness(invocation_script=sb.ToArray(), verification_script=self.Verifications[i])
            scripts.append(witness)


        return scripts