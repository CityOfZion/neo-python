from boa.blockchain.vm.Neo.Transaction import Transaction

class Block():

    @property
    def TransactionCount(self):
        return GetTransactionCount(self)

    @property
    def Transactions(self):
        return GetTransactions(self)



def GetTransactionCount(block) -> int:
    pass


def GetTransactions(block) -> list:
    pass




def GetTransaction(block, index) -> Transaction:
    pass

