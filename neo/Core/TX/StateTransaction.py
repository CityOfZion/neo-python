from neo.Core.TX.Transaction import Transaction, TransactionType
from neo.Core.Fixed8 import Fixed8
from neo.Core.Size import GetVarSize


class StateTransaction(Transaction):

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """

        return super(StateTransaction, self).Size() + GetVarSize(self.Descriptors)

    def __init__(self, *args, **kwargs):
        """
        Create an instance.

        Args:
            *args:
            **kwargs:
        """
        super(StateTransaction, self).__init__(*args, **kwargs)

        self.Type = TransactionType.StateTransaction
        self.Descriptors = None

    def SystemFee(self):
        amount = Fixed8.Zero()
        for d in self.Descriptors:
            amount += d.SystemFee
        return amount

    def DeserializeExclusiveData(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neo.IO.BinaryReader):

        Raises:
            Exception: If the transaction type is incorrect or if there are no claims.
        """
        self.Type = TransactionType.StateTransaction

        self.Descriptors = reader.ReadSerializableArray('neo.Core.State.StateDescriptor.StateDescriptor')

    def GetScriptHashesForVerifying(self, snapshot):
        """
        Get a list of script hashes for verifying transactions.

        Raises:
            Exception: if there are no valid transactions to claim from.

        Returns:
            list: of UInt160 type script hashes.
        """

        raise NotImplementedError()

    def GetScriptHashesForVerifying_Account(self, descriptor):
        raise NotImplementedError()

    def GetScriptHashesForVerifying_Validator(self, descriptor):
        raise NotImplementedError()

    def SerializeExclusiveData(self, writer):
        """
        Serialize object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        writer.WriteSerializableArray(self.Descriptors)

    def ToJson(self):
        """
        Convert object members to a dictionary that can be parsed as JSON.

        Returns:
             dict:
        """

        json = super(StateTransaction, self).ToJson()
        descriptors = [d.ToJson() for d in self.Descriptors]

        json['descriptors'] = descriptors

        return json

    def Verify(self, snapshot, mempool):
        """
        Verify the transaction.

        Args:
            mempool:

        Returns:
            bool: True if verified. False otherwise.
        """

        for descriptor in self.Descriptors:
            if not descriptor.Verify():
                return False

        return super(StateTransaction, self).Verify(snapshot, mempool)
