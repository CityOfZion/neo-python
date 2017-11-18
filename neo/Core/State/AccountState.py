import sys
import time
import binascii

from logzero import logger
from .StateBase import StateBase

from neo.Cryptography.Crypto import Crypto
from neo.Fixed8 import Fixed8
from neo.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream, StreamManager
from neo.Cryptography.Helper import hash_to_wallet_address
from neo.Cryptography.Crypto import Crypto
from neo.IO.BinaryWriter import BinaryWriter


class AccountState(StateBase):

    ScriptHash = None
    IsFrozen = False
    Votes = []
    Balances = {}

    def __init__(self, script_hash=None, is_frozen=False, votes=None, balances=None):
        self.ScriptHash = script_hash
        self.IsFrozen = is_frozen
        if votes is None:
            self.Votes = []
        else:
            self.Votes = votes

        if balances is None:
            self.Balances = {}
        else:
            self.Balances = balances

    @property
    def Address(self):
        return Crypto.ToAddress(self.ScriptHash)

    @property
    def AddressBytes(self):
        return self.Address.encode('utf-8')

    def Clone(self):
        return AccountState(self.ScriptHash, self.IsFrozen, self.Votes, self.Balances)

    def FromReplica(self, replica):
        return AccountState(replica.ScriptHash, replica.IsFrozen, replica.Votes, replica.Balances)

    def Size(self):
        return super(AccountState, self).Size() + sys.getsizeof(self.ScriptHash)

    @staticmethod
    def DeserializeFromDB(buffer):
        m = StreamManager.GetStream(buffer)
        reader = BinaryReader(m)
        account = AccountState()
        account.Deserialize(reader)

        StreamManager.ReleaseStream(m)

        return account

    def Deserialize(self, reader):

        super(AccountState, self).Deserialize(reader)
        self.ScriptHash = reader.ReadUInt160()
        self.IsFrozen = reader.ReadBool()
        num_votes = reader.ReadVarInt()
        for i in range(0, num_votes):
            self.Votes.append(reader.ReadBytes(33))

        num_balances = reader.ReadVarInt()
        self.Balances = {}
        for i in range(0, num_balances):
            assetid = reader.ReadUInt256()
            amount = reader.ReadFixed8()
            self.Balances[assetid] = amount

#        logger.info("balances: %s %s " % (len(self.Balances),self.Balances))

    def Serialize(self, writer):
        super(AccountState, self).Serialize(writer)
        writer.WriteUInt160(self.ScriptHash)
        writer.WriteBool(self.IsFrozen)
        writer.WriteVarInt(len(self.Votes))
        for vote in self.Votes:
            writer.WriteBytes(vote)

        blen = len(self.Balances)
        writer.WriteVarInt(blen)

        for key, fixed8 in self.Balances.items():
            writer.WriteUInt256(key)
            writer.WriteFixed8(fixed8)

    def HasBalance(self, assetId):
        for key, fixed8 in self.Balances.items():
            if key == assetId:
                return True
        return False

    def BalanceFor(self, assetId):
        for key, fixed8 in self.Balances.items():
            if key == assetId:
                return fixed8
        return Fixed8(0)

    def SetBalanceFor(self, assetId, fixed8_val):
        found = False
        for key, val in self.Balances.items():
            if key == assetId:
                self.Balances[key] = fixed8_val
                found = True

        if not found:
            self.Balances[assetId] = fixed8_val

    def AddToBalance(self, assetId, fixed8_val):
        found = False
        for key, balance in self.Balances.items():
            if key == assetId:
                self.Balances[assetId] = self.Balances[assetId] + fixed8_val
                found = True
        if not found:
            self.Balances[assetId] = fixed8_val

    def SubtractFromBalance(self, assetId, fixed8_val):
        found = False
        for key, balance in self.Balances.items():
            if key == assetId:
                self.Balances[assetId] = self.Balances[assetId] - fixed8_val
                found = True
        if not found:
            self.Balances[assetId] = fixed8_val * Fixed8(-1)

    def AllBalancesZeroOrLess(self):
        for key, fixed8 in self.Balances.items():
            if fixed8.value > 0:
                return False
        return True

    def ToByteArray(self):
        ms = StreamManager.GetStream()
        writer = BinaryWriter(ms)
        self.Serialize(writer)

        retval = ms.ToArray()
        StreamManager.ReleaseStream(ms)

        return retval

    def ToJson(self):
        json = super(AccountState, self).ToJson()
        addr = Crypto.ToAddress(self.ScriptHash)

        json['script_hash'] = addr
        json['frozen'] = self.IsFrozen
        json['votes'] = [v.hex() for v in self.Votes]

        balances = {}
        for key, value in self.Balances.items():
            balances[key.ToString()] = str(value.value / Fixed8.D)

        json['balances'] = balances
        return json
