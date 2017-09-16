from neo.SmartContract.Framework.FunctionCode import FunctionCode

expected = b'55c56b6c766b00527ac46c766b51527ac46c766b52527ac46c766b53527ac4616c766b00c36c766b51c3936c766b52c36c766b53c395946c766b54527ac46203006c766b54c3616c7566'


class SCTest(FunctionCode):

    @staticmethod
    def Main(a, b, c, d):

        return a + b - c * d
