from neo.Core.Blockchain import Blockchain
from neo.Wallets.NEP5Token import NEP5Token
from neo.Core.TX.ClaimTransaction import ClaimTransaction
from neo.Core.TX.Transaction import ContractTransaction
from neo.Core.TX.Transaction import TransactionOutput
from neo.Core.TX.TransactionAttribute import TransactionAttribute, TransactionAttributeUsage
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neo.Network.NodeLeader import NodeLeader
from neo.Prompt.Utils import get_asset_id, get_from_addr, get_arg
from neo.Wallets.utils import to_aes_key
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neocore.Fixed8 import Fixed8
from neocore.UInt160 import UInt160
from neocore.KeyPair import KeyPair
from prompt_toolkit import prompt
import binascii
import json
import os
import math
from neo.Implementations.Wallets.peewee.Models import Account
from neo.Prompt.CommandBase import CommandBase, CommandDesc, ParameterDesc
from neo.Prompt.PromptData import PromptData
from neo.Prompt.Commands.Send import CommandWalletSend, CommandWalletSendMany, CommandWalletSign
from neo.Prompt.Commands.Tokens import CommandWalletToken
from neo.logging import log_manager
from neocore.Utils import isValidPublicAddress

logger = log_manager.getLogger()


class CommandWallet(CommandBase):
    def __init__(self):
        super().__init__()

        self.register_sub_command(CommandWalletCreate())
        self.register_sub_command(CommandWalletOpen())
        self.register_sub_command(CommandWalletClose())
        self.register_sub_command(CommandWalletVerbose(), ['v', '--v'])
        self.register_sub_command(CommandWalletCreateAddress())
        self.register_sub_command(CommandWalletDeleteAddress())
        self.register_sub_command(CommandWalletSend())
        self.register_sub_command(CommandWalletSendMany())
        self.register_sub_command(CommandWalletSign())
        self.register_sub_command(CommandWalletClaimGas())
        self.register_sub_command(CommandWalletRebuild())
        self.register_sub_command(CommandWalletAlias())
        self.register_sub_command(CommandWalletToken())
        self.register_sub_command(CommandWalletImport())

    def command_desc(self):
        return CommandDesc('wallet', 'manage wallets')

    def execute(self, arguments):
        wallet = PromptData.Wallet
        item = get_arg(arguments)

        # Create and Open must be handled specially.
        if item in {'create', 'open'}:
            return self.execute_sub_command(item, arguments[1:])

        if not wallet:
            print("Please open a wallet")
            return

        if not item:
            print("Wallet %s " % json.dumps(wallet.ToJson(), indent=4))
            return wallet

        try:
            return self.execute_sub_command(item, arguments[1:])
        except KeyError:
            print(f"{item} is an invalid parameter")
            return


class CommandWalletCreate(CommandBase):

    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        if PromptData.Wallet:
            PromptData.close_wallet()
        path = get_arg(arguments, 0)

        if not path:
            print("Please specify a path")
            return

        if os.path.exists(path):
            print("File already exists")
            return

        passwd1 = prompt("[password]> ", is_password=True)
        passwd2 = prompt("[password again]> ", is_password=True)

        if passwd1 != passwd2 or len(passwd1) < 10:
            print("Please provide matching passwords that are at least 10 characters long")
            return

        password_key = to_aes_key(passwd1)

        try:
            PromptData.Wallet = UserWallet.Create(path=path, password=password_key)
            contract = PromptData.Wallet.GetDefaultContract()
            key = PromptData.Wallet.GetKey(contract.PublicKeyHash)
            print("Wallet %s" % json.dumps(PromptData.Wallet.ToJson(), indent=4))
            print("Pubkey %s" % key.PublicKey.encode_point(True))
        except Exception as e:
            print("Exception creating wallet: %s" % e)
            PromptData.Wallet = None
            if os.path.isfile(path):
                try:
                    os.remove(path)
                except Exception as e:
                    print("Could not remove {}: {}".format(path, e))
            return

        if PromptData.Wallet:
            PromptData.Prompt.start_wallet_loop()
            return PromptData.Wallet

    def command_desc(self):
        p1 = ParameterDesc('path', 'path to store the wallet file')
        return CommandDesc('create', 'create a new NEO wallet (with 1 address)', [p1])


class CommandWalletOpen(CommandBase):

    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        if PromptData.Wallet:
            PromptData.close_wallet()

        path = get_arg(arguments, 0)

        if not path:
            print("Please specify a path")
            return

        if not os.path.exists(path):
            print("Wallet file not found")
            return

        passwd = prompt("[password]> ", is_password=True)
        password_key = to_aes_key(passwd)

        try:
            PromptData.Wallet = UserWallet.Open(path, password_key)

            PromptData.Prompt.start_wallet_loop()
            print("Opened wallet at %s" % path)
            return PromptData.Wallet
        except Exception as e:
            print("Could not open wallet: %s" % e)

    def command_desc(self):
        p1 = ParameterDesc('path', 'path to open the wallet file')
        return CommandDesc('open', 'open a NEO wallet', [p1])


class CommandWalletClose(CommandBase):

    def __init__(self):
        super().__init__()

    def execute(self, arguments=None):
        return PromptData.close_wallet()

    def command_desc(self):
        return CommandDesc('close', 'close the open NEO wallet')


class CommandWalletVerbose(CommandBase):

    def __init__(self):
        super().__init__()

    def execute(self, arguments=None):
        print("Wallet %s " % json.dumps(PromptData.Wallet.ToJson(verbose=True), indent=4))
        return True

    def command_desc(self):
        return CommandDesc('verbose', 'show additional wallet details')


class CommandWalletCreateAddress(CommandBase):

    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        addresses_to_create = get_arg(arguments, 0)

        if not addresses_to_create:
            print("Please specify a number of addresses to create.")
            return

        return CreateAddress(PromptData.Wallet, addresses_to_create)

    def command_desc(self):
        p1 = ParameterDesc('number of addresses', 'number of addresses to create')
        return CommandDesc('create_addr', 'create a new wallet address', params=[p1])


class CommandWalletDeleteAddress(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        addr_to_delete = get_arg(arguments, 0)

        if not addr_to_delete:
            print("Please specify an address to delete.")
            return False

        return DeleteAddress(PromptData.Wallet, addr_to_delete)

    def command_desc(self):
        p1 = ParameterDesc('address', 'address to delete')
        return CommandDesc('delete_addr', 'delete a wallet address', params=[p1])


class CommandWalletClaimGas(CommandBase):

    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        from_addr_str = None

        args = arguments
        if args:
            args, from_addr_str = get_from_addr(args)

        return ClaimGas(PromptData.Wallet, True, from_addr_str)

    def command_desc(self):
        p1 = ParameterDesc('--from-addr', 'source address to claim gas from (if not specified, take first address in wallet)', optional=True)
        return CommandDesc('claim', 'claim gas', params=[p1])


class CommandWalletRebuild(CommandBase):

    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        PromptData.Prompt.stop_wallet_loop()

        start_block = get_arg(arguments, 0, convert_to_int=True)
        if not start_block or start_block < 0:
            start_block = 0
        print(f"Restarting at block {start_block}")

        PromptData.Wallet.Rebuild(start_block)

        PromptData.Prompt.start_wallet_loop()

    def command_desc(self):
        p1 = ParameterDesc('start_block', 'block number to start the resync at', optional=True)
        return CommandDesc('rebuild', 'rebuild the wallet index', params=[p1])


class CommandWalletAlias(CommandBase):

    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        if len(arguments) < 2:
            print("Please supply an address and an alias")
            return False

        return AddAlias(PromptData.Wallet, arguments[0], arguments[1])

    def command_desc(self):
        p1 = ParameterDesc('address', 'address to create an alias for')
        p2 = ParameterDesc('alias', 'alias to associate with the address')
        return CommandDesc('alias', 'create an alias for an address', params=[p1, p2])


class CommandWalletImport(CommandBase):

    def __init__(self):
        super().__init__()
        self.register_sub_command(CommandWalletImportWIF())
        self.register_sub_command(CommandWalletImportNEP2())
        self.register_sub_command(CommandWalletImportWatchAddr())

    def command_desc(self):
        return CommandDesc('import', 'import wallet items')

    def execute(self, arguments):
        item = get_arg(arguments)

        if not item:
            print(f"Please specify an action. See help for available actions")
            return False

        try:
            return self.execute_sub_command(item, arguments[1:])
        except KeyError:
            print(f"{item} is an invalid parameter")
            return False


class CommandWalletImportWIF(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        wallet = PromptData.Wallet

        if len(arguments) != 1:
            print("Please specify the required parameter")
            return False

        wif = arguments[0]
        try:
            kp = KeyPair.PrivateKeyFromWIF(wif)
        except ValueError as e:
            print(f"WIF Error: {str(e)}")
            return False

        try:
            key = wallet.CreateKey(kp)
            print(f"Imported key: {wif}")
            pub_key = key.PublicKey.encode_point(True).decode('utf-8')
            print(f"Pubkey: {pub_key}")
            print(f"Address: {key.GetAddress()}")

        except Exception as e:
            # couldn't find an exact call that throws this but it was in the old code. Leaving it in for now.
            print(f"Key creation error: {str(e)}")
            return False

        return True

    def command_desc(self):
        p1 = ParameterDesc('key', 'private key record in WIF format')
        return CommandDesc('wif', 'import an unprotected private key record of an address', [p1])


class CommandWalletImportNEP2(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        wallet = PromptData.Wallet

        if len(arguments) != 1:
            print("Please specify the required parameters")
            return False

        nep2_key = arguments[0]
        passphrase = prompt("[key password] ", is_password=True)

        try:
            kp = KeyPair.PrivateKeyFromNEP2(nep2_key, passphrase)
        except ValueError as e:
            print(str(e))
            return False

        try:
            key = wallet.CreateKey(kp)
            print(f"Imported key: {nep2_key}")
            pub_key = key.PublicKey.encode_point(True).decode('utf-8')
            print(f"Pubkey: {pub_key}")
            print(f"Address: {key.GetAddress()}")

        except Exception as e:
            # couldn't find an exact call that throws this but it was in the old code. Leaving it in for now.
            print(f"Key creation error: {str(e)}")
            return False

    def command_desc(self):
        p1 = ParameterDesc('private key', 'a NEP-2 protected private key')
        return CommandDesc('nep2', 'import a passphrase protected private key record (NEP-2 format)', [p1])


class CommandWalletImportWatchAddr(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        wallet = PromptData.Wallet

        if len(arguments) != 1:
            print("Please specify the required parameters")
            return False

        addr = arguments[0]
        if not isValidPublicAddress(addr):
            print("Invalid address specified")
            return False

        try:
            addr_script_hash = wallet.ToScriptHash(addr)
            wallet.AddWatchOnly(addr_script_hash)
        except ValueError as e:
            print(str(e))
            return False

        print(f"Added address {addr} as watch-only")
        return True

    def command_desc(self):
        p1 = ParameterDesc('address', 'a public NEO address to watch')
        return CommandDesc('watch_addr', 'import a public address as watch only', [p1])

#########################################################################
#########################################################################


def CreateAddress(wallet, args):
    try:
        int_args = int(args)
    except (ValueError, TypeError) as error:  # for non integer args or Nonetype
        print(error)
        return None

    if wallet is None:
        print("Please open a wallet.")
        return None

    if int_args <= 0:
        print('Enter a number greater than 0.')
        return None

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


def ImportToken(wallet, contract_hash):
    if wallet is None:
        print("please open a wallet")
        return False

    contract = Blockchain.Default().GetContract(contract_hash)

    if contract:
        hex_script = binascii.hexlify(contract.Code.Script)
        token = NEP5Token(script=hex_script)

        result = token.Query()

        if result:
            wallet.AddNEP5Token(token)
            print("added token %s " % json.dumps(token.ToJson(), indent=4))
        else:
            print("Could not import token")


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


def ClaimGas(wallet, require_password=True, from_addr_str=None):
    """
    Args:
        wallet:
        require_password:
        from_addr_str:
    Returns:
        (claim transaction, relayed status)
            if successful: (tx, True)
            if unsuccessful: (None, False)
    """
    if not wallet:
        print("Please open a wallet")
        return None, False

    unclaimed_coins = wallet.GetUnclaimedCoins()

    unclaimed_count = len(unclaimed_coins)
    if unclaimed_count == 0:
        print("no claims to process")
        return None, False

    unclaimed_coin_refs = [coin.Reference for coin in unclaimed_coins]

    available_bonus = Blockchain.Default().CalculateBonusIgnoreClaimed(unclaimed_coin_refs)

    if available_bonus == Fixed8.Zero():
        print("No gas to claim")
        return None, False

    claim_tx = ClaimTransaction()
    claim_tx.Claims = unclaimed_coin_refs
    claim_tx.Attributes = []
    claim_tx.inputs = []

    script_hash = wallet.GetChangeAddress()

    # the following can be used to claim gas that is in an imported contract_addr
    # example, wallet claim --from-addr={smart contract addr}
    if from_addr_str:
        script_hash = wallet.ToScriptHash(from_addr_str)
        standard_contract = wallet.GetStandardAddress()
        claim_tx.Attributes = [TransactionAttribute(usage=TransactionAttributeUsage.Script,
                                                    data=standard_contract.Data)]

    claim_tx.outputs = [
        TransactionOutput(AssetId=Blockchain.SystemCoin().Hash, Value=available_bonus, script_hash=script_hash)
    ]

    context = ContractParametersContext(claim_tx)
    wallet.Sign(context)

    print("\n---------------------------------------------------------------")
    print(f"Will make claim for {available_bonus.ToString()} GAS")
    print("------------------------------------------------------------------\n")

    if require_password:
        print("Enter your password to complete this claim")

        passwd = prompt("[Password]> ", is_password=True)

        if not wallet.ValidatePassword(passwd):
            print("incorrect password")
            return None, False

    if context.Completed:

        claim_tx.scripts = context.GetScripts()

        print("claim tx: %s " % json.dumps(claim_tx.ToJson(), indent=4))

        relayed = NodeLeader.Instance().Relay(claim_tx)

        if relayed:
            print("Relayed Tx: %s " % claim_tx.Hash.ToString())
            wallet.SaveTransaction(claim_tx)
        else:
            print("Could not relay tx %s " % claim_tx.Hash.ToString())
        return claim_tx, relayed

    else:
        print("could not sign tx")

    return None, False


def ShowUnspentCoins(wallet, args):
    addr = None
    asset_type = None
    watch_only = 0
    do_count = False
    try:
        for item in args:
            if len(item) == 34:
                addr = wallet.ToScriptHash(item)
            elif len(item) > 1:
                asset_type = get_asset_id(wallet, item)
            if item == '--watch':
                watch_only = 64
            elif item == '--count':
                do_count = True

    except Exception as e:
        print("Invalid arguments specified")

    if asset_type:
        unspents = wallet.FindUnspentCoinsByAsset(asset_type, from_addr=addr, watch_only_val=watch_only)
    else:
        unspents = wallet.FindUnspentCoins(from_addr=addr, watch_only_val=watch_only)

    if do_count:
        print('\n-----------------------------------------------')
        print('Total Unspent: %s' % len(unspents))
        return unspents

    for unspent in unspents:
        print('\n-----------------------------------------------')
        print(json.dumps(unspent.ToJson(), indent=4))

    return unspents


def SplitUnspentCoin(wallet, args, prompt_passwd=True):
    """
    example ``wallet split Ab8RGQEWetkhVqXjPHeGN9LJdbhaFLyUXz neo 1 100``
    this would split the second unspent neo vin into 100 vouts
    :param wallet:
    :param args (list): A list of arguments as [Address, asset type, unspent index, divisions]
    :return: bool
    """

    fee = Fixed8.Zero()

    try:
        addr = wallet.ToScriptHash(args[0])
        asset = get_asset_id(wallet, args[1])
        index = int(args[2])
        divisions = int(args[3])

        if len(args) == 5:
            fee = Fixed8.TryParse(args[4])

    except Exception as e:
        logger.info("Invalid arguments specified: %s " % e)
        return None

    try:
        unspentItem = wallet.FindUnspentCoinsByAsset(asset, from_addr=addr)[index]
    except Exception as e:
        logger.info("Could not find unspent item for asset with index %s %s :  %s" % (asset, index, e))
        return None

    outputs = split_to_vouts(asset, addr, unspentItem.Output.Value, divisions)

    # subtract a fee from the first vout
    if outputs[0].Value > fee:
        outputs[0].Value -= fee
    else:
        raise Exception("Fee could not be subtracted from outputs.")

    contract_tx = ContractTransaction(outputs=outputs, inputs=[unspentItem.Reference])

    ctx = ContractParametersContext(contract_tx)
    wallet.Sign(ctx)

    print("Splitting: %s " % json.dumps(contract_tx.ToJson(), indent=4))
    if prompt_passwd:
        passwd = prompt("[Password]> ", is_password=True)
        if not wallet.ValidatePassword(passwd):
            print("incorrect password")
            return None

    if ctx.Completed:

        contract_tx.scripts = ctx.GetScripts()

        relayed = NodeLeader.Instance().Relay(contract_tx)

        if relayed:
            wallet.SaveTransaction(contract_tx)
            print("Relayed Tx: %s " % contract_tx.Hash.ToString())
            return contract_tx
        else:
            print("Could not relay tx %s " % contract_tx.Hash.ToString())

    return None


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
