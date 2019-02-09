import json
from neo.Prompt.PromptData import PromptData
from neo.Prompt import Utils as PromptUtils
from neo.Prompt.CommandBase import CommandBase, CommandDesc, ParameterDesc
from neo.Implementations.Wallets.peewee.Models import Account
from neocore.Utils import isValidPublicAddress
from neocore.Fixed8 import Fixed8
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neo.Network.NodeLeader import NodeLeader
from prompt_toolkit import prompt
from neo.Core.Blockchain import Blockchain
from neo.Core.TX.Transaction import ContractTransaction
from neo.Core.TX.Transaction import TransactionOutput
from neo.Prompt.PromptPrinter import prompt_print as print

import sys


class CommandWalletAddress(CommandBase):
    def __init__(self):
        super().__init__()
        self.register_sub_command(CommandWalletCreateAddress())
        self.register_sub_command(CommandWalletDeleteAddress())
        self.register_sub_command(CommandWalletSplit())
        self.register_sub_command(CommandWalletAlias())

    def execute(self, arguments):
        wallet = PromptData.Wallet
        item = PromptUtils.get_arg(arguments)

        if not wallet:
            print("Please open a wallet")
            return

        try:
            return self.execute_sub_command(item, arguments[1:])
        except KeyError:
            print(f"{item} is an invalid parameter")
            return

    def command_desc(self):
        return CommandDesc('address', 'address related operations')


class CommandWalletCreateAddress(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        addresses_to_create = PromptUtils.get_arg(arguments, 0)

        if not addresses_to_create:
            print("Please specify the required parameter")
            return

        return CreateAddress(PromptData.Wallet, addresses_to_create)

    def command_desc(self):
        p1 = ParameterDesc('count', 'number of addresses to create')
        return CommandDesc('create', 'add an address to the wallet', params=[p1])


class CommandWalletDeleteAddress(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        addr_to_delete = PromptUtils.get_arg(arguments, 0)

        if not addr_to_delete:
            print("Please specify the required parameter")
            return False

        return DeleteAddress(PromptData.Wallet, addr_to_delete)

    def command_desc(self):
        p1 = ParameterDesc('address', 'address to delete')
        return CommandDesc('delete', 'delete an address from the wallet', params=[p1])


class CommandWalletSplit(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        wallet = PromptData.Wallet

        if len(arguments) < 4:
            print("Please specify the required parameters")
            return

        if len(arguments) > 5:
            # the 5th argument is the optional attributes,
            print("Too many parameters supplied. Please check your command")
            return

        addr = arguments[0]
        if not isValidPublicAddress(addr):
            print("Invalid address specified")
            return

        try:
            from_addr = wallet.ToScriptHash(addr)
        except ValueError as e:
            print(str(e))
            return

        asset_id = PromptUtils.get_asset_id(wallet, arguments[1])
        if not asset_id:
            print(f"Unknown asset id: {arguments[1]}")
            return

        try:
            index = int(arguments[2])
        except ValueError:
            print(f"Invalid unspent index value: {arguments[2]}")
            return

        try:
            divisions = int(arguments[3])
        except ValueError:
            print(f"Invalid divisions value: {arguments[3]}")
            return

        if divisions < 2:
            print("Divisions cannot be lower than 2")
            return

        if len(arguments) == 5:
            fee = Fixed8.TryParse(arguments[4], require_positive=True)
            if not fee:
                print(f"Invalid fee value: {arguments[4]}")
                return
        else:
            fee = Fixed8.Zero()

        return SplitUnspentCoin(wallet, asset_id, from_addr, index, divisions, fee)

    def command_desc(self):
        p1 = ParameterDesc('address', 'address to split from')
        p2 = ParameterDesc('asset', 'type of asset to split (NEO/GAS)')
        p3 = ParameterDesc('unspent_index', 'index of the vin to split')
        p4 = ParameterDesc('divisions', 'number of vouts to divide into ')
        p5 = ParameterDesc('fee', 'Attach GAS amount to give your transaction priority (> 0.001) e.g. --fee=0.01', optional=True)
        return CommandDesc('split', 'split an asset unspent output into N outputs', params=[p1, p2, p3, p4, p5])


class CommandWalletAlias(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        if len(arguments) < 2:
            print("Please specify the required parameters")
            return False

        return AddAlias(PromptData.Wallet, arguments[0], arguments[1])

    def command_desc(self):
        p1 = ParameterDesc('address', 'address to create an alias for')
        p2 = ParameterDesc('alias', 'custom name to associate with the address')
        return CommandDesc('alias', 'create an alias for an address', params=[p1, p2])


def CreateAddress(wallet, args):
    try:
        int_args = int(args)
    except (ValueError, TypeError) as error:  # for non integer args or Nonetype
        print(error)
        return

    if wallet is None:
        print("Please open a wallet.")
        return

    if int_args <= 0:
        print('Enter a number greater than 0.')
        return

    address_list = []
    for _ in range(int_args):
        keys = wallet.CreateKey()
        account = Account.get(PublicKeyHash=keys.PublicKeyHash.ToBytes())
        address_list.append(account.contract_set[0].Address.ToString())
    print("Created %s new addresses: " % int_args, address_list)
    return wallet


def DeleteAddress(wallet, addr):
    try:
        scripthash = wallet.ToScriptHash(addr)
        error_str = ""

        success, _ = wallet.DeleteAddress(scripthash)
    except ValueError as e:
        success = False
        error_str = f" with error: {e}"

    if success:
        print(f"Deleted address {addr}")
    else:
        print(f"Error deleting addr {addr}{error_str}")

    return success


def AddAlias(wallet, addr, title):
    if wallet is None:
        print("Please open a wallet")
        return False

    try:
        script_hash = wallet.ToScriptHash(addr)
        wallet.AddNamedAddress(script_hash, title)
        return True
    except Exception as e:
        print(e)
        return False


def SplitUnspentCoin(wallet, asset_id, from_addr, index, divisions, fee=Fixed8.Zero(), prompt_passwd=True):
    """
    Split unspent asset vins into several vouts

    Args:
        wallet (neo.Wallet): wallet to show unspent coins from.
        asset_id (UInt256): a bytearray (len 32) representing an asset on the blockchain.
        from_addr (UInt160): a bytearray (len 20) representing an address.
        index (int): index of the unspent vin to split
        divisions (int): number of vouts to create
        fee (Fixed8): A fee to be attached to the Transaction for network processing purposes.
        prompt_passwd (bool): prompt password before processing the transaction

    Returns:
        neo.Core.TX.Transaction.ContractTransaction: contract transaction created
    """

    if wallet is None:
        print("Please open a wallet.")
        return

    unspent_items = wallet.FindUnspentCoinsByAsset(asset_id, from_addr=from_addr)
    if not unspent_items:
        print(f"No unspent assets matching the arguments.")
        return

    if index < len(unspent_items):
        unspent_item = unspent_items[index]
    else:
        print(f"unspent-items: {unspent_items}")
        print(f"Could not find unspent item for asset {asset_id} with index {index}")
        return

    outputs = split_to_vouts(asset_id, from_addr, unspent_item.Output.Value, divisions)

    # subtract a fee from the first vout
    if outputs[0].Value > fee:
        outputs[0].Value -= fee
    else:
        print("Fee could not be subtracted from outputs.")
        return

    contract_tx = ContractTransaction(outputs=outputs, inputs=[unspent_item.Reference])

    ctx = ContractParametersContext(contract_tx)
    wallet.Sign(ctx)

    print("Splitting: %s " % json.dumps(contract_tx.ToJson(), indent=4))
    if prompt_passwd:
        passwd = prompt("[Password]> ", is_password=True)
        if not wallet.ValidatePassword(passwd):
            print("incorrect password")
            return

    if ctx.Completed:
        contract_tx.scripts = ctx.GetScripts()

        relayed = NodeLeader.Instance().Relay(contract_tx)

        if relayed:
            wallet.SaveTransaction(contract_tx)
            print("Relayed Tx: %s " % contract_tx.Hash.ToString())
            return contract_tx
        else:
            print("Could not relay tx %s " % contract_tx.Hash.ToString())


def split_to_vouts(asset, addr, input_val, divisions):
    divisor = Fixed8(divisions)

    new_amounts = input_val / divisor
    outputs = []
    total = Fixed8.Zero()

    if asset == Blockchain.Default().SystemShare().Hash:
        if new_amounts % Fixed8.FD() > Fixed8.Zero():
            new_amounts = new_amounts.Ceil()

    while total < input_val:
        if total + new_amounts < input_val:
            outputs.append(TransactionOutput(asset, new_amounts, addr))
            total += new_amounts
        else:
            diff = input_val - total
            outputs.append(TransactionOutput(asset, diff, addr))
            total += diff

    return outputs
