from neo.SmartContract.Framework.Neo.Storage import Storage
from neo.SmartContract.Framework.FunctionCode import FunctionCode


class Math(FunctionCode):

    @staticmethod
    def Main(operation, a, b):

        if operation == 'add':

            return a + b

        elif operation == 'sub':

            return a - b

        return None