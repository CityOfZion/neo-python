from neo.SmartContract.Framework.FunctionCode import FunctionCode


class SCTest(FunctionCode):

    @staticmethod
    def Main(a, b):

        c = a + b

        if c == 'hellogoodbye':

            return a + b + a + b


        return 1
