# -*- coding:utf-8 -*-
"""
Description:
    Signature Context
Usage:
    from AntShares.Core.SingatureContext import SingatureContext
"""

from AntShares.Wallets.ContractParameterType import ContractParameterType
from AntShares.Core.ScriptBuilder import ScriptBuilder


class SingatureContext(BytesIO):
    """docstring for SingatureContext"""
    def __init__(self, signable):
        super(SingatureContext, self).__init__()
        self.signable = signable
        self.scriptHashes = self.signable.getScriptHashesForVerifying()
        self.redeemScripts = [ None for i in len(self.scriptHashes)]
        self.signatures = [ None for i in len(self.scriptHashes)]
        self.completed = [ False for i in len(self.scriptHashes)]

    def isCompleted(self):
        for x in self.completed:
            if x == False:
                return False
        else:
            return True

    def add(self, contract, pubkey, signature):
        for scripthash in self.scriptHashes:
            if scripthash == contract.scriptHash:
                i = self.scriptHashes.index(scripthash)
                if  self.redeemScripts[i] == None:
                    self.redeemScripts[i] = contract.redeemScript
                if self.signatures[i] == None:
                    self.signatures[i] = (pubkey.toString(), signature)

                completed = (contract.parameterList.length == len(self.signatures[i]))  # TODO contract.parameterList
                for param in contract.parameterList:
                    if param != ContractParameterType.Signature
                    completed = False

                this.completed[i] |= completed
                return True
        else:
            return False

    def getScripts(self):
        if not isCompleted:
            raise Exception, "isCompleted == False"
        scripts = [ None for i in len(self.signatures)]
        for script in self.scripts:
            i = self.scripts.index(script)
            array = [{'pubkey':key, 'signature': signature} for (signature, key) in self.signatures[i]]
            array.sort(key=lambda x: x['pubkey'])
            sb = ScriptBuilder()
            for item in array:
                sb.push(item['signature'])
            scripts[i] = Script()
            scripts[i].stackScript = sb.toArray()
            scripts[i].redeemScript = self.redeemScripts[i]

        return scripts
