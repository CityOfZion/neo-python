
from neocore.IO.Mixins import SerializableMixin
import sys
from neocore.Cryptography.Helper import *
from neo.Core.Helper import Helper
from neo.Network.InventoryType import InventoryType


class ConsensusPayload(SerializableMixin):

    InventoryType = InventoryType.Consensus
    Version = None
    PrevHash = None
    BlockIndex = None
    ValidatorIndex = None
    Timestamp = None
    Data = []
    Witness = None

    _hash = None

    def Hash(self):
        if not self._hash:
            self._hash = bin_dbl_sha256(Helper.GetHashData(self))
        return self._hash

    def Size(self):
        raise NotImplementedError()

    def GetMessage(self):
        return Helper.GetHashData(self)

    def GetScriptHashesForVerifying(self):
        raise NotImplementedError()

    def Deserialize(self, reader):
        raise NotImplementedError('Consensus not implemented')

    def DeserializeUnsigned(self, reader):
        raise NotImplementedError()

    def Serialize(self, writer):
        raise NotImplementedError()

    def SerializeUnsigned(self, writer):
        raise NotImplementedError()

    def Verify(self):
        raise NotImplementedError()
