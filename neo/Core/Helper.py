
from neo.Cryptography.Crypto import *
from neo.IO.BinaryWriter import BinaryWriter
from neo.IO.MemoryStream import MemoryStream
import pickle

class Helper(object):


    @staticmethod
    def WeightedFilter(list):
        raise NotImplementedError()

    @staticmethod
    def WeightedAverage(list):
        raise NotImplementedError()

    @staticmethod
    def GetHashData(hashable):
        ms = MemoryStream()
        writer = BinaryWriter(ms)
        hashable.SerializeUnsigned(writer)
        ms.flush()
        return ms.ToArray()

    @staticmethod
    def Sign(signable, keypair):

        raise NotImplementedError()

    @staticmethod
    def ToArray( value ):

        ms = MemoryStream()
        writer = BinaryWriter(ms)

        value.Serialize(writer)

        return ms.ToArray()

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

    @staticmethod
    def IToBA(value):
        return [1 if digit == '1' else 0 for digit in bin(value)[2:]]
