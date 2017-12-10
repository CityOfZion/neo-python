from neo.VM.Mixins import ScriptTableMixin


class CachedScriptTable(ScriptTableMixin):

    contracts = None

    def __init__(self, contracts):
        self.contracts = contracts

    def GetScript(self, script_hash):

        contract = self.contracts.TryGet(script_hash)

        if contract is not None:
            return contract.Code.Script

        return None

    def GetContractState(self, script_hash):

        contract = self.contracts.TryGet(script_hash)

        return contract
