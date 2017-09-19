from neo.SmartContract.Framework.FunctionCode import FunctionCode

class SCTest(FunctionCode):

    @staticmethod
    def Main(a, b, c, d):

        a2 = a * 2

        b2 = b + 1

        c2 = c / 2

        d2 = d - 1


        return a2 + b2 + c2 + d2


#    @staticmethod
#    def dostuff(a, b):
#
#        return a + b
