from neo.SmartContract.Framework.FunctionCode import FunctionCode

expected = b'53c56b6c766b00527ac46c766b51527ac4616c766b51c36c766b52527ac46203006c766b52c3616c7566'


class SCTest(FunctionCode):

    @staticmethod
    def Main(a: int, b: int) -> int:

        return b
