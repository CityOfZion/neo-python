from neo.SmartContract.Contract import Contract,ContractType
from neo.SmartContract.ContractParameterType import ContractParameterType
from neo.VM.ScriptBuilder import ScriptBuilder
from neo.VM import OpCode
from neo.Core.Witness import Witness
import json
import binascii
import pdb

class ContractParamater():


    Type = None
    Value = None

    def __init__(self, type):
        self.Type = type

class ContextItem():

    Script = None
    ContractParameters = None
    Signatures = None

    def __init__(self, contract):
        self.Script = contract.Script
        self.ContractParameters = []
        for b in bytearray(contract.ParameterList):
            p = ContractParamater(b)
            self.ContractParameters.append(p)

class ContractParametersContext():


    Verifiable = None

    ScriptHashes = None

    ContextItems = None

    def __init__(self, verifiable):

        self.Verifiable = verifiable
        self.ScriptHashes = verifiable.GetScriptHashesForVerifying()

        self.ContextItems = {}

    @property
    def Completed(self):

        if len(self.ContextItems) < len(self.ScriptHashes):
            print("context items, script hashes %s %s " % (self.ContextItems, self.ScriptHashes))
            return False

        for item in self.ContextItems.values():
            print("going through items %s " % item.Script)
            if item is None:
                print("item is none...")
                return False

            for p in item.ContractParameters:
                print("item parameters??? %s" % p)
                if p is None or p.Value is None:
                    print("parameter is none")
                    return False

        return True


    def Add(self, contract, index, parameter):

        item = self.CreateItem(contract)
        print("ADDING iTEM:: %s " % item)
        item.ContractParameters[index].Value = parameter

#        pdb.set_trace()

        return True


    def CreateItem(self, contract):

        if contract.ScriptHash.ToBytes() in self.ContextItems.keys():
            return self.ContextItems[ contract.ScriptHash.ToBytes()]

        if not contract.ScriptHash in self.ScriptHashes:
            print("script hash not in self script hashes...")
            return None

        item = ContextItem(contract)

        self.ContextItems[contract.ScriptHash.ToBytes()] = item

        return item


    def AddSignature(self, contract, pubkey, signature):

        if contract.Type == ContractType.MultiSigContract:

            raise NotImplementedError('Multi sig contracts not yet implemented')


        else:

            index = -1
            length = len(contract.ParameterList)
            for i in range(0, length):

                if contract.ParameterList[i] == ContractParameterType.Signature:
                    if index >=0:
                        raise Exception("Signature must be first")
                    else:
                        index = i

            print("ADDING SIG!! .... %s %s %s " % (contract, index,signature))
            return self.Add(contract, index, signature)

    def GetIndex(self, script_hash):
        for index, hash in enumerate(self.ScriptHashes):
            if hash == script_hash:
                return index
        return -1



    def GetParameters(self, script_hash):
        if script_hash.ToBytes() in self.ContextItems.keys():
            return self.ContextItems[script_hash.ToBytes()].Parameters

    def GetParameter(self, scriptHash, index):
        params = self.GetParameters(scriptHash)
        if params:
            return params[index]
        return None


    def GetScripts(self):

        if not self.Completed:
            raise Exception("Signature Context not complete")

        scripts = []

        for i in range(0, len(self.ScriptHashes)):

            item = self.ContextItems[self.ScriptHashes[i].ToBytes()]
            print("GETTING SCRIPTS, item is %s " % item)

            sb = ScriptBuilder()

            plist = list(item.ContractParameters)
            plist.reverse()

            for p in plist:
                sb.push(p.Value)

            vscript = bytearray(0)

            if item.Script is not None:
                vscript = item.Script

            witness = Witness(
                invocation_script=sb.ToArray(),
                verification_script=vscript
            )

            scripts.append(witness)


        return scripts