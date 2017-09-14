from neo.SmartContract.Framework.FunctionCode import FunctionCode

expected = b'56c56b6c766b00527ac46c766b51527ac4616c766b00c36c766b51c3846c766b52527ac46c766b52c36c766b51c3856c766b53527ac46c766b00c36c766b53c3866c766b54527ac46c766b54c36c766b55527ac46203006c766b55c3616c7566'

#note bitwise << and >> are not working...

class SCTest(FunctionCode):


    @staticmethod
    def Main(a, b):

        j = a & b

        q = j | b

        m = a ^ q

        return m

