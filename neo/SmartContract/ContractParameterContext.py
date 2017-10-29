from neo.Core.TX.Transaction import ContractTransaction
from neo.SmartContract.Contract import Contract,ContractType
from neo.SmartContract.ContractParameterType import ContractParameterType,ToName
from neo.VM.ScriptBuilder import ScriptBuilder
from neo.IO.MemoryStream import MemoryStream
from neo.IO.BinaryReader import BinaryReader
from neo.IO.BinaryWriter import BinaryWriter
from neo.VM import OpCode
from neo.Core.Witness import Witness
import json
import binascii
import pdb
from neo.Core.FunctionCode import FunctionCode

class ContractParamater():


    Type = None
    Value = None

    def __init__(self, type):
        self.Type = type


    def ToJson(self):
        jsn = {}
        jsn['type'] = ToName(self.Type)
        return jsn


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

    def ToJson(self):
        jsn = {}
        if self.Script is not None:
            if type(self.Script) is str:
                jsn['script'] = self.Script
            else:
                jsn['script'] = self.Script.decode()
        jsn['parameters'] = [p.ToJson() for p in self.ContractParameters]
        if self.Signatures is not None:
            jsn['signatures'] = {}
            for key, value in self.Signatures.items():
                if value is not None:
                    if type(value) is str:
                        jsn['signatures'][key] = value
                    else:
                        jsn['signatures'][key] = value.decode()
                else:
                    print("Seems like {} has empty signature".format(key))
        return jsn


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
            print("CONTEXT ITEMS, SCRIPT HASHES %s %s " % (len(self.ContextItems), len(self.ScriptHashes)))
            return False

        for item in self.ContextItems.values():
            if item is None:
                print("ITEM IN CONTEXT ITEMS IS NONE!!")
                return False

            for p in item.ContractParameters:
                if p is None or p.Value is None:
                    return False
                if p.Type is not None:
                    if p.Value == 0:
                        return False
        return True


    def Add(self, contract, index, parameter):

        item = self.CreateItem(contract)
        item.ContractParameters[index].Value = parameter

#        pdb.set_trace()

        return True


    def CreateItem(self, contract):

        if contract.ScriptHash.ToBytes() in self.ContextItems.keys():
            return self.ContextItems[ contract.ScriptHash.ToBytes()]

        if not contract.ScriptHash in self.ScriptHashes:
            return None

        item = ContextItem(contract)

        self.ContextItems[contract.ScriptHash.ToBytes()] = item

        return item



    def AddSignature(self, contract, pubkey, signature):

        if contract.Type == ContractType.MultiSigContract:

            item = self.CreateItem(contract)
            if item is None:
                return False
            for p in item.ContractParameters:
                if p.Value is not None:
                    return False
            if item.Signatures is None:
                item.Signatures = {}
            elif item.Signatures.ContainsKey(pubkey.encode_point(True)):
                return False

            points = []
            temp = binascii.unhexlify(contract.Script)
            ms = MemoryStream(binascii.unhexlify(contract.Script))
            reader = BinaryReader(ms)
            numr = reader.ReadUInt8()
            while reader.ReadUInt8() == 33:
                points.append(binascii.hexlify(reader.ReadBytes(33)))
            ms.close()

            if pubkey.encode_point(True) not in points:
                return False

            item.Signatures[pubkey.encode_point(True).decode()] = binascii.hexlify(signature)

            if len(item.Signatures) == len(contract.ParameterList):
                for k in points:
                    if self.Add(contract, i, item.Signatures[k]) == None:
                        raise Exception("Invalid operation")
                item.Signatures = None
            return True

        else:

            index = -1
            length = len(contract.ParameterList)
            for i in range(0, length):

                if contract.ParameterList[i] == ContractParameterType.Signature:
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

            sb = ScriptBuilder()

            plist = list(item.ContractParameters)
            plist.reverse()

            for p in plist:

                sb.push(p.Value)

            vscript = bytearray(0)

            if item.Script is not None:
                if type(item.Script) is str:
                    item.Script = item.Script.encode('utf-8')
                vscript = item.Script
#                print("SCRIPT IS %s " % item.Script)

            witness = Witness(
#                invocation_script='40fdb984faf0a400b6894c1ce5b317cf894ba3eb89b899cefda2ac307b278418b943534ad298884f9200dc4b7e1dc244db16c62a44a830a860060ec11d3e6e9717',
                invocation_script=sb.ToArray(),
                verification_script=vscript
            )

            scripts.append(witness)


        return scripts


    def ToJson(self):
        jsn = {}
        jsn['type'] = 'Neo.Core.ContractTransaction'  # Verifiable.GetType().FullName
        ms = MemoryStream()
        w = BinaryWriter(ms)
        self.Verifiable.SerializeUnsigned(w)
        ms.flush()
        jsn['hex'] = ms.ToArray().decode()
        jsn['items'] = {}
        for key, value in self.ContextItems.items():
            if type(key) == str:
                shkey = "0x{}".format(key)
            else:
                shkey = "0x{}".format(key.decode())
            jsn['items'][shkey] = value.ToJson()

        return jsn


    def FromJson(jsn):
        try:
            parsed = json.loads(jsn)
            if parsed['type'] == 'Neo.Core.ContractTransaction':
                verifiable = ContractTransaction()
                ms = MemoryStream(binascii.unhexlify(parsed['hex']))
                r = BinaryReader(ms)
                verifiable.DeserializeUnsigned(r)
                context = ContractParametersContext(verifiable)
                for key, value in parsed['items'].items():
                    if "0x" in key:
                        key = key[2:]
                    parameterbytes = []
                    for pt in value['parameters']:
                        if pt['type'] == 'Signature':
                            parameterbytes.append(0)
                    contract = Contract.Create(value['script'], parameterbytes, value['signatures'])
                    context.ContextItems[key] = ContextItem(contract)
                return context
            else:
                raise ("Unsupported transaction type in JSON")

        except Exception as e:
            print("Failed to import ContractParametersContext from JSON: {}".format(e))

