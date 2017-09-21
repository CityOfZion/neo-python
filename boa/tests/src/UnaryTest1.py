from neo.SmartContract.Framework.FunctionCode import FunctionCode

class SCTest(FunctionCode):

    @staticmethod
    def Main():

        a = 1

        b = True

        c = True

        if a and c and b:

            return 8

        return 3

