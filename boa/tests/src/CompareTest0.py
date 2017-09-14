from neo.SmartContract.Framework.FunctionCode import FunctionCode

expected = b'53c56b6c766b00527ac46c766b51527ac461006c766b52527ac46c766b00c36c766b51c3a06c766b52527ac4616c7566'


class SCTest(FunctionCode):


    @staticmethod
    def Main(a, b):

        j = False


        j = a > b

