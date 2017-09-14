from neo.SmartContract.Framework.FunctionCode import FunctionCode

expected = b'56c56b61516c766b00527ac4526c766b51527ac4536c766b52527ac4546c766b53527ac46c766b00c36c766b51c3936c766b52c36c766b53c395946c766b54527ac46c766b54c36c766b55527ac46203006c766b55c3616c7566'


class SCTest(FunctionCode):

    @staticmethod
    def Main():

        a = 1
        b = 2
        c = 3
        e = 4
        d = a + b - c * e

        return d


