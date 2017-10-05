
class Account():

    @property
    def ScriptHash(self):
        return GetScriptHash(self)

    @property
    def Votes(self):
        return GetVotes(self)



def GetScriptHash(account):
    pass


def GetVotes(account):
    pass



def SetVotes(account, votes):
    pass


def GetBalance(account, asset_id):
    pass