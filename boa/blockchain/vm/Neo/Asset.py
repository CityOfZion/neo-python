
class Asset():

    @property
    def AssetId(self):
        return GetAssetId(self)

    @property
    def AssetType(self):
        return GetAssetType(self)

    @property
    def Amount(self):
        return GetAmount(self)

    @property
    def Available(self):
        return GetAvailable(self)

    @property
    def Precision(self):
        return GetPrecision(self)

    @property
    def Owner(self):
        return GetOwner(self)

    @property
    def Admin(self):
        return GetAdmin(self)

    @property
    def Issuer(self):
        return GetIssuer(self)




def GetAssetId(asset):
    pass


def GetAssetType(asset):
    pass


def GetAmount(asset):
    pass


def GetAvailable(asset):
    pass


def GetPrecision(asset):
    pass


def GetOwner(asset):
    pass


def GetAdmin(asset):
    pass


def GetIssuer(asset):
    pass



def Create(asset_type, name, amount, precision, owner, admin, issuer):
    pass


def Renew(asset, years):
    pass

