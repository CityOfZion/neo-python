from neo.Storage.Common.Snapshot import Snapshot


class CloneSnapshot(Snapshot):

    def __init__(self, snapshot):
        self.PersistingBlock = snapshot.PersistingBlock
        self.Blocks = snapshot.Blocks.CreateSnapshot()
        self.Transactions = snapshot.Transactions.CreateSnapshot()
        self.Accounts = snapshot.Accounts.CreateSnapshot()
        self.SpentCoins = snapshot.SpentCoins.CreateSnapshot()
        self.UnspentCoins = snapshot.UnspentCoins.CreateSnapshot()
        self.Assets = snapshot.Assets.CreateSnapshot()
        self.Validators = snapshot.Validators.CreateSnapshot()
        self.Contracts = snapshot.Contracts.CreateSnapshot()
        self.Storages = snapshot.Storages.CreateSnapshot()
