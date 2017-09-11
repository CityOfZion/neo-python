from neo.SmartContract.Framework.Neo.Storage import Storage,StorageContext
from neo.SmartContract.Framework.FunctionCode import FunctionCode



class Math(FunctionCode):

    q = 1 # type: int

    def Main(operation: str, a: int, b: int) -> int:

        j = 4 # type: int

        if operation == 'add':

            return a + b

        elif operation == 'sub':

            return a - b


        return j