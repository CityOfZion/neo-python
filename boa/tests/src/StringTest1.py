from neo.SmartContract.Framework.FunctionCode import FunctionCode


class SCTest(FunctionCode):

    @staticmethod
    def Main(a):


        if a == 'hello':

            return 2


        return 1
