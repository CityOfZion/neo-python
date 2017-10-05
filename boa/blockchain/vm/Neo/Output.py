
class TransactionOutput():

    @property
    def AssetId(self):
        return GetAssetId(self)

    @property
    def Value(self):
        return GetValue(self)

    @property
    def ScriptHash(self):
        return GetScriptHash(self)



def GetAssetId(output):
    pass


def GetValue(output):
    pass


def GetScriptHash(output):
    pass

