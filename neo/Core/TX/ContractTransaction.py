

from neo.Core.TX.Transaction import Transaction,TransactionType

class ContractTransaction(Transaction):


    def __init__(self, *args, **kwargs):
        super(ContractTransaction, self).__init__(*args, **kwargs)
        self.Type = TransactionType.ContractTransaction

    def DeserializeExclusiveData(self, reader):
        self.Type = TransactionType.ContractTransaction

