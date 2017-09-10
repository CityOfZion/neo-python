from neo.SmartContract.Framework.Neo.Storage import Storage,StorageContext
from neo.SmartContract.Framework.FunctionCode import FunctionCode



class Math(FunctionCode):

    q = 1

    @staticmethod
    def Main(operation, a, b):

        j = 0

        if operation == 'add':

            return a + b

        elif operation == 'sub':

            return a - b

#        def what(a):
#            return b


        return None