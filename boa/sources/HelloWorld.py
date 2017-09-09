from neo.SmartContract.Framework.FunctionCode import FunctionCode
from neo.SmartContract.Framework.Neo.Storage import Storage


class HelloWorld(FunctionCode):

    @staticmethod
    def Main():

        Storage.Put(Storage.CurrentContext(), "Hello", "World")