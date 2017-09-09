from neo.SmartContract.Framework.FunctionCode import FunctionCode


class Math(FunctionCode):

    @staticmethod
    def Main(operation, a, b):
        
        if operation == 'add':
            r = a + b
        elif operation == 'sub':
            r = a - b
        else:
            r = None
            
        return r

