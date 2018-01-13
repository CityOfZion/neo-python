import json
import binascii
import pdb

from logzero import logger

from neo.Core.TX.Transaction import ContractTransaction
from neo.SmartContract.Contract import Contract, ContractType
from neo.SmartContract.ContractParameterType import ContractParameterType, ToName
from neo.VM.ScriptBuilder import ScriptBuilder
from neo.IO.MemoryStream import MemoryStream
from neocore.IO.BinaryReader import BinaryReader
from neocore.IO.BinaryWriter import BinaryWriter
from neo.VM import OpCode
from neo.Core.Witness import Witness
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
                    logger.info("Seems like {} has empty signature".format(key))
        return jsn


class ContractParametersContext():

    Verifiable = None

    ScriptHashes = None

    ContextItems = None

    IsMultiSig = None

    def __init__(self, verifiable, isMultiSig=False):

        self.Verifiable = verifiable
        self.ScriptHashes = verifiable.GetScriptHashesForVerifying()
        self.ContextItems = {}
        self.IsMultiSig = isMultiSig

    @property
    def Completed(self):

        if len(self.ContextItems) < len(self.ScriptHashes):
            return False

        for item in self.ContextItems.values():
            if item is None:
                return False

            for p in item.ContractParameters:

                # for multi signature contracts, we need to make sure
                # that this check runs
                if self.IsMultiSig:
                    if p is None or p.Value is None:
                        return False
                    if p.Type is not None:
                        if p.Value == 0:
                            return False

                # for non-multisig contracts ( specifically, sending from contract
                # addresses that have more than one param ) we need to allow an empty
                # value, or, if it is empty, to fill it with 0
                else:
                    if p is None or p.Value is None:
                        if p.Type is not None:
                            p.Value = 0

        return True

    def Add(self, contract, index, parameter):

        item = self.CreateItem(contract)
        item.ContractParameters[index].Value = parameter

#        pdb.set_trace()

        return True

    def CreateItem(self, contract):

        if contract.ScriptHash.ToBytes() in self.ContextItems.keys():
            return self.ContextItems[contract.ScriptHash.ToBytes()]

        if contract.ScriptHash not in self.ScriptHashes:
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
            elif pubkey.encode_point(True) in item.Signatures:
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
                i = 0
                points.sort(reverse=True)
                for k in points:
                    if k.decode() in item.Signatures:
                        if self.Add(contract, i, item.Signatures[k.decode()]) is None:
                            raise Exception("Invalid operation")
                        i += 1
                item.Signatures = None
            return True

        else:

            index = -1
            length = len(contract.ParameterList)
            for i in range(0, length):

                if contract.ParameterList[i] == ContractParameterType.Signature:
                    if index >= 0:
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
                if type(p.Value) is list:
                    pa = p.Value
                    pa.reverse()
                    listlength = len(pa)
                    for listitem in pa:
                        sb.push(listitem)
                    sb.push(listlength)
                    sb.Emit(OpCode.PACK)
                else:
                    sb.push(p.Value)

            vscript = bytearray(0)

            if item.Script is not None:
                if type(item.Script) is str:
                    item.Script = item.Script.encode('utf-8')
                vscript = item.Script
#                logger.info("SCRIPT IS %s " % item.Script)

            witness = Witness(
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

    def FromJson(jsn, isMultiSig=True):
        try:
            parsed = json.loads(jsn)
            if parsed['type'] == 'Neo.Core.ContractTransaction':
                verifiable = ContractTransaction()
                ms = MemoryStream(binascii.unhexlify(parsed['hex']))
                r = BinaryReader(ms)
                verifiable.DeserializeUnsigned(r)
                context = ContractParametersContext(verifiable, isMultiSig=isMultiSig)
                for key, value in parsed['items'].items():
                    if "0x" in key:
                        key = key[2:]
                    key = key.encode()
                    parameterbytes = []
                    for pt in value['parameters']:
                        if pt['type'] == 'Signature':
                            parameterbytes.append(0)
                    contract = Contract.Create(value['script'], parameterbytes, key)
                    context.ContextItems[key] = ContextItem(contract)
                    if 'signatures' in value:
                        context.ContextItems[key].Signatures = value['signatures']

                return context
            else:
                raise ("Unsupported transaction type in JSON")

        except Exception as e:
            logger.error("Failed to import ContractParametersContext from JSON: {}".format(e))
