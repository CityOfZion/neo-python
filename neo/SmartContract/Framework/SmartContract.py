from neo.VM import OpCode
from neo.SmartContract.Framework.Decorator import op_decorate


class SmartContract():

    @op_decorate(OpCode.SHA1)
    @staticmethod
    def Sha1(data):
        pass
        

    @op_decorate(OpCode.SHA256)
    @staticmethod
    def Sha256(data):
        pass


    @op_decorate(OpCode.HASH160)
    @staticmethod
    def Hash160(data):
        pass


    @op_decorate(OpCode.SHA256)
    @staticmethod
    def Hash256(data):
        pass
        

    @op_decorate(OpCode.CHECKSIG)
    @staticmethod
    def VerifySignature(pubkey, signature):
        pass