
class TransactionInput():

    @property
    def Hash(self):
        return GetHash(self)

    @property
    def Index(self):
        return GetIndex(self)


def GetHash(input):
    pass


def GetIndex(input):
    pass