from neo.SmartContract.Framework.FunctionCode import FunctionCode
from neo.SmartContract.Framework.Neo.Storage import Blah

j = 223232


class SCTest(FunctionCode):

    @staticmethod
    def Main():

        a = 1
        b = 2
        c = a + b

        return c


#    @staticmethod
#    def dostuff(a, b):
#
#        return a + b
