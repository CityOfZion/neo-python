from neo.Blockchain import GetBlockchain,GetStateReader
from neo.Cryptography.Crypto import *
from neo.IO.BinaryWriter import BinaryWriter
from neo.IO.MemoryStream import MemoryStream,StreamManager
from neo.UInt160 import UInt160
from neo.VM.ScriptBuilder import ScriptBuilder
from neo.SmartContract.ApplicationEngine import ApplicationEngine
from neo.Fixed8 import Fixed8
from neo.SmartContract import TriggerType
from neo import Settings
from base58 import b58decode
import pdb
class Helper(object):


    @staticmethod
    def WeightedFilter(list):
        raise NotImplementedError()

    @staticmethod
    def WeightedAverage(list):
        raise NotImplementedError()

    @staticmethod
    def GetHashData(hashable):
        ms = StreamManager.GetStream()
        writer = BinaryWriter(ms)
        hashable.SerializeUnsigned(writer)
        ms.flush()
        retVal = ms.ToArray()
        StreamManager.ReleaseStream(ms)
        return retVal



    @staticmethod
    def Sign(verifiable, keypair):

        prikey = bytes(keypair.PrivateKey)
        hashdata = verifiable.GetHashData()
        res = Crypto.Default().Sign(hashdata, prikey, keypair.PublicKey)
        return res

    @staticmethod
    def ToArray( value ):

        ms = StreamManager.GetStream()
        writer = BinaryWriter(ms)

        value.Serialize(writer)

        retVal = ms.ToArray()
        StreamManager.ReleaseStream(ms)
        
        return retVal


    @staticmethod
    def AddrStrToScriptHash(address):
        data = b58decode(address)
        if len(data) != 25:
            raise ValueError('Not correct Address, wrong length.')
        if data[0] != Settings.ADDRESS_VERSION:
            raise ValueError('Not correct Coin Version')

        checksum = Crypto.Default().Hash256(data[:21])[:4]
        if checksum != data[21:]:
            raise Exception('Address format error')
        return UInt160(data=data[1:21])

    @staticmethod
    def ToScriptHash(scripts):
        return Crypto.Hash160(scripts)


    @staticmethod
    def RawBytesToScriptHash(raw):
        rawh = binascii.unhexlify(raw)

        rawhashstr = binascii.unhexlify(bytes(Crypto.Hash160(rawh), encoding='utf-8'))
#        h160bytes = bytearray(rawhashstr)
#        h160bytes.reverse()
#        out = bytes(h160bytes.hex(), encoding='utf-8')
#        return out
        return UInt160(data=rawhashstr)

    @staticmethod
    def VerifyScripts(verifiable):



        try:
            hashes = verifiable.GetScriptHashesForVerifying()
        except Exception as e:
            print("couldng get script hashes %s " % e)
            return False

        if len(hashes) != len(verifiable.Scripts):
            print("hashes not same length as verifiable scripts")
            return False

        for i in range(0, len(hashes)):
            verification = verifiable.Scripts[i].VerificationScript


            if len(verification) == 0:
#                print("VERIFICATION IS 0, EMITTING APP CALL")
                sb = ScriptBuilder()
                sb.EmitAppCall(hashes[i].Data)
                verification = sb.ToArray()

            else:
                verification_hash = Crypto.ToScriptHash(verification,unhex=False)
                if hashes[i] != verification_hash:
                    print("hashes not equal to script hash!")
                    return False

            engine = ApplicationEngine(TriggerType.Verification, verifiable, GetBlockchain(), GetStateReader(), Fixed8.Zero())
            engine.LoadScript(verification, False)
            invoction = verifiable.Scripts[i].InvocationScript
            engine.LoadScript(invoction, True)

            res =  engine.Execute()
            if not res:
                print("engine did not execute")
                return False

            if engine.EvaluationStack.Count != 1 or not engine.EvaluationStack.Pop().GetBoolean():
                return False

        return True

    @staticmethod
    def IToBA(value):
        return [1 if digit == '1' else 0 for digit in bin(value)[2:]]
