from base58 import b58decode
from neo.Blockchain import GetBlockchain, GetStateReader
from neocore.Cryptography.Crypto import *
from neocore.IO.BinaryWriter import BinaryWriter
from neocore.UInt160 import UInt160
from neo.IO.MemoryStream import StreamManager
from neo.VM.ScriptBuilder import ScriptBuilder
from neo.SmartContract.ApplicationEngine import ApplicationEngine
from neocore.Fixed8 import Fixed8
from neo.SmartContract import TriggerType
from neo.Settings import settings
from neo.EventHub import events


class Helper(object):

    @staticmethod
    def WeightedFilter(list):
        raise NotImplementedError()

    @staticmethod
    def WeightedAverage(list):
        raise NotImplementedError()

    @staticmethod
    def GetHashData(hashable):
        """
        Get the data used for hashing.

        Args:
            hashable (neo.IO.Mixins.SerializableMixin): object extending SerializableMixin

        Returns:
            bytes:
        """
        ms = StreamManager.GetStream()
        writer = BinaryWriter(ms)
        hashable.SerializeUnsigned(writer)
        ms.flush()
        retVal = ms.ToArray()
        StreamManager.ReleaseStream(ms)
        return retVal

    @staticmethod
    def Sign(verifiable, keypair):
        """
        Sign the `verifiable` object with the private key from `keypair`.

        Args:
            verifiable:
            keypair (neocore.KeyPair):

        Returns:
            bool: True if successfully signed. False otherwise.
        """
        prikey = bytes(keypair.PrivateKey)
        hashdata = verifiable.GetHashData()
        res = Crypto.Default().Sign(hashdata, prikey)
        return res

    @staticmethod
    def ToArray(value):
        """
        Serialize the given `value` to a an array of bytes.

        Args:
            value (neo.IO.Mixins.SerializableMixin): object extending SerializableMixin.

        Returns:
            bytes:
        """
        ms = StreamManager.GetStream()
        writer = BinaryWriter(ms)

        value.Serialize(writer)

        retVal = ms.ToArray()
        StreamManager.ReleaseStream(ms)

        return retVal

    @staticmethod
    def AddrStrToScriptHash(address):
        """
        Convert a public address to a script hash.

        Args:
            address (str): base 58 check encoded public address.

        Raises:
            ValueError: if the address length of address version is incorrect.
            Exception: if the address checksum fails.

        Returns:
            UInt160:
        """
        data = b58decode(address)
        if len(data) != 25:
            raise ValueError('Not correct Address, wrong length.')
        if data[0] != settings.ADDRESS_VERSION:
            raise ValueError('Not correct Coin Version')

        checksum = Crypto.Default().Hash256(data[:21])[:4]
        if checksum != data[21:]:
            raise Exception('Address format error')
        return UInt160(data=data[1:21])

    @staticmethod
    def ToScriptHash(scripts):
        """
        Get a hash of the provided message using the ripemd160 algorithm.

        Args:
            scripts (str): message to hash.

        Returns:
            str: hash as a double digit hex string.
        """
        return Crypto.Hash160(scripts)

    @staticmethod
    def RawBytesToScriptHash(raw):
        """
        Get a hash of the provided raw bytes using the ripemd160 algorithm.

        Args:
            raw (bytes): byte array of raw bytes. i.e. b'\xAA\xBB\xCC'

        Returns:
            UInt160:
        """
        rawh = binascii.unhexlify(raw)
        rawhashstr = binascii.unhexlify(bytes(Crypto.Hash160(rawh), encoding='utf-8'))
        return UInt160(data=rawhashstr)

    @staticmethod
    def VerifyScripts(verifiable):
        """
        Verify the scripts of the provided `verifiable` object.

        Args:
            verifiable (neo.IO.Mixins.VerifiableMixin):

        Returns:
            bool: True if verification is successful. False otherwise.
        """
        try:
            hashes = verifiable.GetScriptHashesForVerifying()
        except Exception as e:
            logger.error("couldn't get script hashes %s " % e)
            return False

        if len(hashes) != len(verifiable.Scripts):
            return False

        blockchain = GetBlockchain()

        for i in range(0, len(hashes)):
            verification = verifiable.Scripts[i].VerificationScript

            if len(verification) == 0:
                sb = ScriptBuilder()
                sb.EmitAppCall(hashes[i].Data)
                verification = sb.ToArray()

            else:
                verification_hash = Crypto.ToScriptHash(verification, unhex=False)
                if hashes[i] != verification_hash:
                    return False

            state_reader = GetStateReader()
            engine = ApplicationEngine(TriggerType.Verification, verifiable, blockchain, state_reader, Fixed8.Zero())
            engine.LoadScript(verification, False)
            invoction = verifiable.Scripts[i].InvocationScript
            engine.LoadScript(invoction, True)

            try:
                success = engine.Execute()
                state_reader.ExecutionCompleted(engine, success)
            except Exception as e:
                state_reader.ExecutionCompleted(engine, False, e)

            if engine.EvaluationStack.Count != 1 or not engine.EvaluationStack.Pop().GetBoolean():
                Helper.EmitServiceEvents(state_reader)
                return False

            Helper.EmitServiceEvents(state_reader)

        return True

    @staticmethod
    def IToBA(value):
        return [1 if digit == '1' else 0 for digit in bin(value)[2:]]

    @staticmethod
    def EmitServiceEvents(state_reader):
        for event in state_reader.events_to_dispatch:
            events.emit(event.event_type, event)
