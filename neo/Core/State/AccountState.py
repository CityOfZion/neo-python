
from .StateBase import StateBase
import sys
import binascii
from neo.Fixed8 import Fixed8
from neo.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream,StreamManager
from autologging import logged
import time
from neo.Cryptography.Helper import hash_to_wallet_address

@logged
class AccountState(StateBase):



    ScriptHash = None
    IsFrozen = False
    Votes = []
    Balances = {}


    def __init__(self, script_hash=None, is_frozen=False, votes=[], balances={}):
        self.ScriptHash = script_hash
        self.IsFrozen = is_frozen
        self.Votes = votes
        self.Balances = balances

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
            assetid = binascii.hexlify( reader.ReadUInt256())
            amount = reader.ReadFixed8()
            self.Balances[assetid] = amount

#        self.__log.debug("balances: %s %s " % (len(self.Balances),self.Balances))

    def Serialize(self, writer):
        super(AccountState, self).Serialize(writer)
        writer.WriteUInt160(self.ScriptHash)
        writer.WriteBool(self.IsFrozen)
        writer.WriteVarInt(len(self.Votes))
        for vote in self.Votes:
            writer.WriteBytes(vote)


        blen = len(self.Balances)
        writer.WriteVarInt(blen)

        for key,value in self.Balances.items():
            writer.WriteUInt256(key)
            writer.WriteFixed8(value)

    def HasBalance(self, assetId):
        for key, balance in self.Balances.items():
            if key == assetId:
                return True
        return False

    def BalanceFor(self, assetId):
        for key,balance in self.Balances.items():
            if key == assetId:
                return balance
        return Fixed8(0)

    def SetBalanceFor(self, assetId, val):
        found=False
        for key,balance in self.Balances.items():
            if key == assetId:
                self.Balances[key] = val
                found = True

        if not found:
            self.Balances[assetId] = val

    def AddToBalance(self, assetId, val):
        found = False
        for key, balance in self.Balances.items():
            if key == assetId:
                newval = balance.value + val
                self.Balances[assetId] = Fixed8(newval)
                found = True
        if not found:
            self.Balances[assetId] = val

    def AllBalancesZeroOrLess(self):
        for key,value in self.Balances.items():
            if value.value > 0:
                return False
        return True


    def ToJson(self):
        json = super(AccountState, self).ToJson()
        hash = bytearray(self.ScriptHash)
        addr = hash_to_wallet_address(hash)
        json['script_hash'] = addr
        json['frozen'] = self.IsFrozen
        json['votes'] = []

        balances = {}
        for key, value in self.Balances.items():
            balances[key.decode('utf-8')] = value.value

        json['balances'] = balances
        return json
