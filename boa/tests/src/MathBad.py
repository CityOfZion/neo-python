from neo.SmartContract.Framework.Neo.Storage import Storage, StorageContext
from neo.SmartContract.Framework.FunctionCode import FunctionCode

from neo.BigInteger import BigInteger


class Math(FunctionCode):

    @staticmethod
    def Main(operation, a, b):

        if operation == 'add':

            return a + b

        elif operation == 'sub':

            return a - b

        return None
