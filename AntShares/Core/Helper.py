
from AntShares.Cryptography.Crypto import *

class Helper(object):


    @staticmethod
    def GetHashData(hashable):

        raise NotImplementedError()


    @staticmethod
    def Sign(signable, keypair):

        raise NotImplementedError()


    @staticmethod
    def ToScriptHash(scripts):
        return Crypto.Hash160(scripts)

    @staticmethod
    def VerifyScripts(verifiable):

        max_steps = 3000
        hashes = []

        try:
            hashes = verifiable.GetScriptHashesForVerifying()
        except Exception as e:
            return False

        if len(hashes) != len(verifiable.Scripts): return False

        ### @TODO script hash verifying!

        raise NotImplementedError()

