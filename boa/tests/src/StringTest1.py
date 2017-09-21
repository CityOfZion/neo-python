from neo.SmartContract.Framework.FunctionCode import FunctionCode


class SCTest(FunctionCode):

    @staticmethod
    def Main(a, b):

        c = a + b

        if c == 'hellogoodbye':

            return 3


        return 1
