import binascii
from base58 import b58decode
from neo.Blockchain import GetBlockchain, GetStateMachine
from neo.Storage.Common.CachedScriptTable import CachedScriptTable
from neo.Storage.Common.DBPrefix import DBPrefix
from neo.Core.State.ContractState import ContractState
from neo.Core.State.AssetState import AssetState
from neo.Core.Cryptography.Crypto import Crypto
from neo.Core.IO.BinaryWriter import BinaryWriter
from neo.Core.UInt160 import UInt160
from neo.Core.UInt256 import UInt256
from neo.IO.MemoryStream import StreamManager
from neo.VM.ScriptBuilder import ScriptBuilder
from neo.Core.Fixed8 import Fixed8
from neo.SmartContract import TriggerType
from neo.Settings import settings
from neo.EventHub import events
from neo.logging import log_manager

logger = log_manager.getLogger()


class Helper:

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
            keypair (neo.Core.KeyPair):

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
            bytes: hex formatted bytes
        """
        ms = StreamManager.GetStream()
        writer = BinaryWriter(ms)

        value.Serialize(writer)

        retVal = ms.ToArray()
        StreamManager.ReleaseStream(ms)

        return retVal

    @staticmethod
    def ToStream(value):
        """
        Serialize the given `value` to a an array of bytes.

        Args:
            value (neo.IO.Mixins.SerializableMixin): object extending SerializableMixin.

        Returns:
            bytes: not hexlified
        """
        ms = StreamManager.GetStream()
        writer = BinaryWriter(ms)

        value.Serialize(writer)

        retVal = ms.getvalue()
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
            raw (bytes): byte array of raw bytes. e.g. b'\xAA\xBB\xCC'

        Returns:
            UInt160:
        """
        rawh = binascii.unhexlify(raw)
        rawhashstr = binascii.unhexlify(bytes(Crypto.Hash160(rawh), encoding='utf-8'))
        return UInt160(data=rawhashstr)

    @staticmethod
    def IToBA(value):
        return [1 if digit == '1' else 0 for digit in bin(value)[2:]]

    @staticmethod
    def EmitServiceEvents(state_reader):
        for event in state_reader.events_to_dispatch:
            events.emit(event.event_type, event)

    @staticmethod
    def StaticAssetState(assetId):
        neo = AssetState()
        neo.AssetId = UInt256.ParseString("0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b")
        neo.AssetType = 0x00

        gas = AssetState()
        gas.AssetId = UInt256.ParseString("0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7")
        gas.AssetType = 0x01

        if assetId == neo.AssetId:
            return neo

        elif assetId == gas.AssetId:
            return gas

        else:
            return None
