
from .StateBase import StateBase
import sys
import binascii
from neo.Fixed8 import Fixed8
from neo.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream
from autologging import logged
import time
@logged
class AccountState(StateBase):



    ScriptHash = None
    IsFrozen = False
    Votes = []
    Balances = []


    def __init__(self, script_hash=None, is_frozen=False, votes=[], balances=[]):
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
        m = MemoryStream(buffer)
        reader = BinaryReader(m)
        account = AccountState()
        account.Deserialize(reader)
        return account

    def Deserialize(self, reader):
        start = time.clock()
        super(AccountState, self).Deserialize(reader)
        self.ScriptHash = reader.ReadUInt160()
        self.IsFrozen = reader.ReadBool()
        num_votes = reader.ReadVarInt()
        for i in range(0, num_votes):
            self.Votes.append(reader.ReadBytes(33))

        num_balances = reader.ReadVarInt()

        for i in range(0, num_balances):
            assetid = binascii.hexlify( reader.ReadUInt256())
            amount = reader.ReadFixed8()
            self.Balances.append([assetid,amount])

        self.__log.debug("ACcount state total balances %s " % (len(self.Balances)))
        end = time.clock()
        self.__log.debug("Deserialize %s in time %s " % (self.ScriptHash, end-start))


    def Serialize(self, writer):
        super(AccountState, self).Serialize(writer)
        writer.WriteUInt160(self.ScriptHash)
        writer.WriteBool(self.IsFrozen)
        writer.WriteVarInt(len(self.Votes))
        for vote in self.Votes:
            writer.WriteBytes(vote)

        balances = [b for b in self.Balances if b[1].value > 0]

        writer.WriteVarInt(len(balances))

        for i in range(0, len(balances)):
            balance = balances[i]
            writer.WriteUInt256(balance[0])
            writer.WriteFixed8(balance[1])
#            writer.WriteInt64(balance[1].value)

    def HasBalance(self, assetId):
        for b in self.Balances:
            if b[0] == assetId:
                return True

    def BalanceFor(self, assetId):
        for b in self.Balances:
            if b[0] == assetId:
                return b[1]
        return Fixed8(0)

    def SetBalanceFor(self, assetId, val):
        found=False
        for b in self.Balances:
            if b[0] == assetId:
                b[1] = val
                found=True

        if not found:
            self.Balances.append([assetId,val])

    def AddToBalance(self, assetId, val):
        found = False
        for b in self.Balances:
            if b[0] == assetId:
                b[1] = Fixed8( b[1].value + val)
                found = True

        if not found:
            self.Balances.append([assetId, val])

    def AllBalancesZeroOrLess(self):
        for item in self.Balances:
            if item[1].value > 0:
                return False
        return True