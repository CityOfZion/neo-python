from boa.blockchain.vm.Neo.Header import Header
from boa.blockchain.vm.Neo.Block import Block
from boa.blockchain.vm.Neo.Transaction import Transaction
from boa.blockchain.vm.Neo.Account import Account
from boa.blockchain.vm.Neo.Asset import Asset
from boa.blockchain.vm.Neo.Contract import Contract



def GetHeight() -> int:
    pass

def GetHeader(height_or_hash) -> Header:
    pass

def GetBlock(height_or_hash) -> Block:
    pass


def GetTransaction(hash) -> Transaction:
    pass

def GetAccount(script_hash) -> Account:
    pass


def GetValidators() -> []:
    pass


def GetAsset(asset_id) -> Asset:
    pass


def GetContract(script_hash) -> Contract:
    pass