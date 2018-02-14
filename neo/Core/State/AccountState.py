import sys
from .StateBase import StateBase
from neocore.Fixed8 import Fixed8
from neocore.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import StreamManager
from neocore.Cryptography.Crypto import Crypto
from neocore.IO.BinaryWriter import BinaryWriter


class AccountState(StateBase):

    ScriptHash = None
    IsFrozen = False
    Votes = []
    Balances = {}

    def __init__(self, script_hash=None, is_frozen=False, votes=None, balances=None):
        """
        Create an instance.

        Args:
            script_hash (UInt160):
            is_frozen (bool):
            votes (list): of EllipticCurve.ECPoint items.
            balances (dict):
                Key (UInt256): assetID.
                Value (Fixed8): balance.
        """
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
        """
        Get the accounts public address.

        Returns:
            str: base58 encoded string representing the account address.
        """
        return Crypto.ToAddress(self.ScriptHash)

    @property
    def AddressBytes(self):
        """
        Get the accounts public address.

        Returns:
            bytes: base58 encoded account address.
        """
        return self.Address.encode('utf-8')

    def Clone(self):
        """
        Clone self.

        Returns:
            AccountState:
        """
        return AccountState(self.ScriptHash, self.IsFrozen, self.Votes, self.Balances)

    def FromReplica(self, replica):
        """
        Get AccountState object from a replica.
        Args:
            replica (obj): must have ScriptHash, IsFrozen, Votes and Balances members.

        Returns:
            AccountState:
        """
        return AccountState(replica.ScriptHash, replica.IsFrozen, replica.Votes, replica.Balances)

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        return super(AccountState, self).Size() + sys.getsizeof(self.ScriptHash)

    @staticmethod
    def DeserializeFromDB(buffer):
        """
        Deserialize full object.

        Args:
            buffer (bytes, bytearray, BytesIO): (Optional) data to create the stream from.

        Returns:
            AccountState:
        """
        m = StreamManager.GetStream(buffer)
        reader = BinaryReader(m)
        account = AccountState()
        account.Deserialize(reader)

        StreamManager.ReleaseStream(m)

        return account

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neocore.IO.BinaryReader):
        """
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

    def Serialize(self, writer):
        """
        Serialize full object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
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
        """
        Flag indicating if the asset has a balance.

        Args:
            assetId (UInt256):

        Returns:
            bool: True if a balance is present. False otherwise.
        """
        for key, fixed8 in self.Balances.items():
            if key == assetId:
                return True
        return False

    def BalanceFor(self, assetId):
        """
        Get the balance for a given asset id.

        Args:
            assetId (UInt256):

        Returns:
            Fixed8: balance value.
        """
        for key, fixed8 in self.Balances.items():
            if key == assetId:
                return fixed8
        return Fixed8(0)

    def SetBalanceFor(self, assetId, fixed8_val):
        """
        Set the balance for an asset id.
        Args:
            assetId (UInt256):
            fixed8_val (Fixed8): balance value.
        """
        found = False
        for key, val in self.Balances.items():
            if key == assetId:
                self.Balances[key] = fixed8_val
                found = True

        if not found:
            self.Balances[assetId] = fixed8_val

    def AddToBalance(self, assetId, fixed8_val):
        """
        Add amount to the specified balance.

        Args:
            assetId (UInt256):
            fixed8_val (Fixed8): amount to add.
        """
        found = False
        for key, balance in self.Balances.items():
            if key == assetId:
                self.Balances[assetId] = self.Balances[assetId] + fixed8_val
                found = True
        if not found:
            self.Balances[assetId] = fixed8_val

    def SubtractFromBalance(self, assetId, fixed8_val):
        """
        Subtract amount to the specified balance.

        Args:
            assetId (UInt256):
            fixed8_val (Fixed8): amount to add.
        """
        found = False
        for key, balance in self.Balances.items():
            if key == assetId:
                self.Balances[assetId] = self.Balances[assetId] - fixed8_val
                found = True
        if not found:
            self.Balances[assetId] = fixed8_val * Fixed8(-1)

    def AllBalancesZeroOrLess(self):
        """
        Flag indicating if all balances are 0 or less.

        Returns:
            bool: True if all balances are <= 0. False, otherwise.
        """
        for key, fixed8 in self.Balances.items():
            if fixed8.value > 0:
                return False
        return True

    def ToByteArray(self):
        """
        Serialize self and get the byte stream.

        Returns:
            bytes: serialized object.
        """
        ms = StreamManager.GetStream()
        writer = BinaryWriter(ms)
        self.Serialize(writer)

        retval = ms.ToArray()
        StreamManager.ReleaseStream(ms)

        return retval

    def ToJson(self):
        """
        Convert object members to a dictionary that can be parsed as JSON.

        Returns:
             dict:
        """
        json = super(AccountState, self).ToJson()
        addr = Crypto.ToAddress(self.ScriptHash)

        json['script_hash'] = addr
        json['frozen'] = self.IsFrozen
        json['votes'] = [v.hex() for v in self.Votes]

        balances = {}
        for key, value in self.Balances.items():
            balances[key.To0xString()] = value.ToString()

        json['balances'] = balances
        return json
