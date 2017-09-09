from neo.SmartContract.Framework.Decorator import sys_call


class Storage():

    @sys_call('Neo.Storage.GetContext')
    @staticmethod
    def CurrentContext():
        pass


    @staticmethod
    def Get(context, key):
        pass


    @staticmethod
    def Put(context, key, value):
        pass
        

    @staticmethod
    def Delete(context, key, value):
        pass
