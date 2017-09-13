from neo.SmartContract.Framework.FunctionCode import FunctionCode

expected = b'54c56b6c766b00527ac46c766b51527ac461516c766b52527ac4526c766b53527ac46203006c766b53c3616c7566'


class SCTest(FunctionCode):


    @staticmethod
    def Main(a: int, b: int) -> int:

        j = 1

        return 2


