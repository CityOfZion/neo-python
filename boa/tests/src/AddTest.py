from neo.SmartContract.Framework.FunctionCode import FunctionCode

expected = b'54c56b61516c766b00527ac4526c766b51527ac46c766b00c36c766b51c3936c766b52527ac4516c766b53527ac46203006c766b53c3616c7566'


class SCTest(FunctionCode):

    @staticmethod
    def Main():

        a = 1
        b = 2
        c = a + b

        return c
