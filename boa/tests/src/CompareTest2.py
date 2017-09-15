from neo.SmartContract.Framework.FunctionCode import FunctionCode

expected = b'54c56b6c766b00527ac46c766b51527ac4616c766b00c36c766b51c3a06c766b52527ac46c766b52c3640f0061516c766b53527ac4620f0061006c766b53527ac46203006c766b53c3616c7566'


class SCTest(FunctionCode):


    @staticmethod
    def Main(a, b):


        if a > b:

            return True


        return False



