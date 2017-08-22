from neo.VM.Mixins import ScriptTableMixin


class CachedScriptTable(ScriptTableMixin):

    contracts = None

    def __init__(self, contracts):
        self.contracts = contracts


    def GetScript(self, script_hash):

        return self.contracts.TryGet( script_hash).Code.Script