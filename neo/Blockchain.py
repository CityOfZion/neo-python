def GetBlockchain():
    from neo.Core.Blockchain import Blockchain
    return Blockchain.Default()


def GetGenesis():
    from neo.Core.Blockchain import Blockchain
    return Blockchain.GenesisBlock()


def GetSystemCoin():
    from neo.Core.Blockchain import Blockchain
    return Blockchain.SystemCoin()


def GetSystemShare():
    from neo.Core.Blockchain import Blockchain
    return Blockchain.SystemShare()


def GetStateMachine():
    from neo.SmartContract.StateMachine import StateMachine
    from neo.Storage.Interface.DBInterface import DBInterface
    from neo.Storage.Common.DBPrefix import DBPrefix
    from neo.Core.State.AccountState import AccountState
    from neo.Core.State.AssetState import AssetState
    from neo.Core.State.ValidatorState import ValidatorState
    from neo.Core.State.ContractState import ContractState
    from neo.Core.State.StorageItem import StorageItem

    bc = GetBlockchain()

    accounts = DBInterface(bc._db, DBPrefix.ST_Account, AccountState)
    assets = DBInterface(bc._db, DBPrefix.ST_Asset, AssetState)
    validators = DBInterface(bc._db, DBPrefix.ST_Validator, ValidatorState)
    contracts = DBInterface(bc._db, DBPrefix.ST_Contract, ContractState)
    storages = DBInterface(bc._db, DBPrefix.ST_Storage, StorageItem)

    return StateMachine(accounts, validators, assets, contracts, storages, None, bc)


def GetConsensusAddress(validators):
    from neo.Core.Blockchain import Blockchain
    return Blockchain.GetConsensusAddress(validators)
