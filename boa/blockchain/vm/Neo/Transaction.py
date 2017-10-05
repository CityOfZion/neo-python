
class Transaction():

    @property
    def Hash(self):
        return GetHash(self)

    @property
    def Type(self):
        return GetType(self)

    @property
    def Attributes(self):
        return GetAttributes(self)

    @property
    def Inputs(self):
        return GetInputs(self)

    @property
    def Outputs(self):
        return GetOutputs(self)

    @property
    def References(self):
        return GetReferences(self)




def GetHash(transaction):
    pass


def GetType(transaction):
    pass


def GetAttributes(transaction):
    pass


def GetInputs(transaction):
    pass


def GetOutputs(transaction):
    pass


def GetReferences(transaction):
    pass

