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
from prompt_toolkit import prompt
import binascii
import json
import os
import math
from neo.Implementations.Wallets.peewee.Models import Account
from neo.Prompt.CommandBase import CommandBase, CommandDesc, ParameterDesc
from neo.Prompt.PromptData import PromptData
from neo.Prompt.Commands.Send import CommandWalletSend, CommandWalletSendMany, CommandWalletSign
from neo.logging import log_manager


logger = log_manager.getLogger()


class CommandWallet(CommandBase):
    def __init__(self):
        super().__init__()

        self.register_sub_command('create', CommandWalletCreate())
        self.register_sub_command('open', CommandWalletOpen())
        self.register_sub_command('close', CommandWalletClose())
        self.register_sub_command(['v', '--v', 'verbose'], CommandWalletVerbose())
        self.register_sub_command('migrate', CommandWalletMigrate())
        self.register_sub_command('create_addr', CommandWalletCreateAddress())
        self.register_sub_command('send', CommandWalletSend())
        self.register_sub_command('sendmany', CommandWalletSendMany())
        self.register_sub_command('sign', CommandWalletSign())

    def command_desc(self):
        return CommandDesc('wallet', 'manage wallets')

    def execute(self, arguments):
        wallet = PromptData.Wallet
        item = get_arg(arguments)

        # Create, Open, and Close must be handled specially.
        if item == 'create':
            self.execute_sub_command(item, arguments[1:])
            return
        
        elif item == 'open':
            self.execute_sub_command(item, arguments[1:])
            return
        
        elif item == 'close':
            self.execute_sub_command(item, arguments=None)
            return

        if not wallet:
            print("Please open a wallet")
            return

        if not item:
            print("Wallet %s " % json.dumps(wallet.ToJson(), indent=4))
            return

        try:
            self.execute_sub_command(item, arguments[1:])
        except KeyError:
            print(f"Wallet: {item} is an invalid parameter")


class CommandWalletCreate(CommandBase):

    def __init__(self):
        super().__init__()

    @classmethod
    def execute(cls, arguments):
        if PromptData.Wallet:
            CommandWalletClose.execute(arguments=None)
        path = get_arg(arguments, 0)

        if path:
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

        else:
            print("Please specify a path")

    @classmethod
    def command_desc(cls):
        p1 = ParameterDesc('path', 'path to store the wallet file')
        return CommandDesc('create', 'creates a new NEO wallet address', [p1])


class CommandWalletOpen(CommandBase):

    def __init__(self):
        super().__init__()
    
    @classmethod
    def execute(cls, arguments):
        if PromptData.Wallet:
            CommandWalletClose.execute(arguments=None)

        path = get_arg(arguments, 0)

        if path:

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

        else:
            print("Please specify a path")

    @classmethod
    def command_desc(cls):
        p1 = ParameterDesc('path', 'path to open the wallet file')
        return CommandDesc('open', 'opens a NEO wallet', [p1])


class CommandWalletClose(CommandBase):

    def __init__(self):
        super().__init__()

    @classmethod
    def execute(cls, arguments):
        if PromptData.Wallet:
            path = PromptData.Wallet._path
            PromptData.Prompt.stop_wallet_loop()
            PromptData.Wallet.Close()
            PromptData.Wallet = None
            print("Closed wallet %s" % path)
    
    @classmethod
    def command_desc(cls):
        return CommandDesc('close', 'closes the open NEO wallet')


class CommandWalletVerbose(CommandBase):

    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        print("Wallet %s " % json.dumps(PromptData.Wallet.ToJson(verbose=True), indent=4))

    def command_desc(self):
        return CommandDesc('verbose', 'show additional wallet details')


class CommandWalletMigrate(CommandBase):

    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        if PromptData.Wallet is not None:
            PromptData.Wallet.Migrate()
            print("Migrated wallet")

    def command_desc(self):
        p1 = ParameterDesc('option1', 'description of params 1')
        p2 = ParameterDesc('option2', 'description of params 2')
        p3 = ParameterDesc('option3', 'description of params 3', optional=True)
        params = [p1, p2, p3]
        return CommandDesc('migrate', 'migrate a wallet from y to z', params=params)


class CommandWalletCreateAddress(CommandBase):

    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        addresses_to_create = get_arg(arguments, 0)
        CreateAddress(PromptData.Wallet, addresses_to_create)

    def command_desc(self):
        return CommandDesc('create_addr', 'create a wallet address')


#########################################################################
#########################################################################


def CreateAddress(wallet, args):
    try:
        int_args = int(args)
    except (ValueError, TypeError) as error:  # for non integer args or Nonetype
        print(error)
        return False

    if wallet is None:
        print("Please open a wallet.")
        return False

    if int_args <= 0:
        print('Enter a number greater than 0.')
        return False

    address_list = []
    for i in range(int_args):
        keys = wallet.CreateKey()
        account = Account.get(PublicKeyHash=keys.PublicKeyHash.ToBytes())
        address_list.append(account.contract_set[0].Address.ToString())
    print("Created %s new addresses: " % int_args, address_list)
    return wallet


def DeleteAddress(wallet, addr):
    scripthash = wallet.ToScriptHash(addr)

    success, coins = wallet.DeleteAddress(scripthash)

    if success:
        print("Deleted address %s " % addr)

    else:
        print("error deleting addr %s " % addr)

    return success


def DeleteToken(wallet, contract_hash):
    hash = UInt160.ParseString(contract_hash)

    success = wallet.DeleteNEP5Token(hash)

    if success:
        print("Deleted token %s " % contract_hash)

    else:
        print("error deleting token %s " % contract_hash)

    return False


def ImportWatchAddr(wallet, addr):
    if wallet is None:
        print("Please open a wallet")
        return False

    script_hash = None
    try:
        script_hash = wallet.ToScriptHash(addr)
    except Exception as e:
        pass

    if not script_hash:
        try:
            data = bytearray(binascii.unhexlify(addr.encode('utf-8')))
            data.reverse()
            script_hash = UInt160(data=data)
        except Exception as e:
            pass

    if script_hash:
        wallet.AddWatchOnly(script_hash)
        print("added watch address")
    else:
        print("incorrect format for watch address")


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
    except Exception as e:
        print(e)


def ClaimGas(wallet, require_password=True, args=None):
    """
    Args:
        wallet:
        require_password:
        args:
    Returns:
        (claim transaction, relayed status)
            if successful: (tx, True)
            if unsuccessful: (None, False)
    """
    if args:
        params, from_addr_str = get_from_addr(args)
    else:
        params = None
        from_addr_str = None

    unclaimed_coins = wallet.GetUnclaimedCoins()

    unclaimed_count = len(unclaimed_coins)
    if unclaimed_count == 0:
        print("no claims to process")
        return None, False

    max_coins_per_claim = None
    if params:
        max_coins_per_claim = get_arg(params, 0, convert_to_int=True)
        if not max_coins_per_claim:
            print("max_coins_to_claim must be an integer")
            return None, False
        if max_coins_per_claim <= 0:
            print("max_coins_to_claim must be greater than zero")
            return None, False
    if max_coins_per_claim and unclaimed_count > max_coins_per_claim:
        unclaimed_coins = unclaimed_coins[:max_coins_per_claim]

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
    print("Will make claim for %s GAS" % available_bonus.ToString())
    if max_coins_per_claim and unclaimed_count > max_coins_per_claim:
        print("NOTE: You are claiming GAS on %s unclaimed coins. %s additional claim transactions will be required to claim all available GAS." % (max_coins_per_claim, math.floor(unclaimed_count / max_coins_per_claim)))
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
