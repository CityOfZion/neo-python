from neo.Storage.Common.DataCache import DataCache


class Snapshot:

    def __init__(self):
        self.PersistingBlock = None
        self.Blocks = DataCache()
        self.Transactions = DataCache()
        self.Accounts = DataCache()
        self.UnspentCoins = DataCache()
        self.SpentCoins = DataCache()
        self.Validators = DataCache()
        self.Assets = DataCache()
        self.Contracts = DataCache()
        self.Storages = DataCache()

    def CalculateBonus(self, inputs, ignoreClaimed=True):  # -> Fixed8
        raise NotImplementedError()

    def CalculateBonusToHeight(self, inputs, height_end):  # -> Fixed8
        raise NotImplementedError()

    def CalculateBonusInternal(self, unclaimed):  # -> Fixed8
        raise NotImplementedError()

    def Clone(self):
        raise NotImplementedError()

    def Commit(self):
        # filter out accounts to delete then commit
        self.Accounts.DeleteWhere(lambda key, account: not account.IsFrozen and len(account.Votes) == 0 and account.AllBalancesZeroOrLess())
        self.UnspentCoins.DeleteWhere(lambda key, unspent: unspent.IsAllSpent)
        self.SpentCoins.DeleteWhere(lambda k, spent: len(spent.Items) == 0)

        self.Blocks.Commit()
        self.Transactions.Commit()
        self.Accounts.Commit()
        self.UnspentCoins.Commit()
        self.SpentCoins.Commit()
        self.Validators.Commit()
        self.Assets.Commit()
        self.Contracts.Commit()
        self.Storages.Commit()

    def GetScript(self, script_hash):
        try:
            return self.Contracts[script_hash].Code.Script
        except ValueError:
            return None

    def GetUnclaimed(self, hash):  # should be uint256
        raise NotImplementedError()

    def GetValidators(self):
        raise NotImplementedError()

    def GetValidatorsFromTx(self, others):
        raise NotImplementedError()
