from neo.Core.Blockchain import Blockchain
from neo.Core.TX.ClaimTransaction import ClaimTransaction
from neo.Core.TX.Transaction import TransactionOutput
from neo.Core.TX.TransactionAttribute import TransactionAttribute, TransactionAttributeUsage
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neo.Network.NodeLeader import NodeLeader
from neo.Prompt import Utils as PromptUtils
from neo.Wallets.utils import to_aes_key
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neocore.Fixed8 import Fixed8
from neocore.UInt160 import UInt160
from prompt_toolkit import prompt
import json
import os
from neo.Prompt.CommandBase import CommandBase, CommandDesc, ParameterDesc
from neo.Prompt.PromptData import PromptData
from neo.Prompt.Commands.Send import CommandWalletSend, CommandWalletSendMany, CommandWalletSign
from neo.Prompt.Commands.Tokens import CommandWalletToken
from neo.Prompt.Commands.WalletAddress import CommandWalletAddress
from neo.Prompt.Commands.WalletImport import CommandWalletImport
from neo.Prompt.Commands.WalletExport import CommandWalletExport
from neo.logging import log_manager
from neocore.Utils import isValidPublicAddress
from neo.Prompt.PromptPrinter import prompt_print as print

logger = log_manager.getLogger()


class CommandWallet(CommandBase):
    def __init__(self):
        super().__init__()

        self.register_sub_command(CommandWalletCreate())
        self.register_sub_command(CommandWalletOpen())
        self.register_sub_command(CommandWalletClose())
        self.register_sub_command(CommandWalletVerbose(), ['v', '--v'])
        self.register_sub_command(CommandWalletSend())
        self.register_sub_command(CommandWalletSendMany())
        self.register_sub_command(CommandWalletSign())
        self.register_sub_command(CommandWalletClaimGas())
        self.register_sub_command(CommandWalletRebuild())
        self.register_sub_command(CommandWalletUnspent())
        self.register_sub_command(CommandWalletToken())
        self.register_sub_command(CommandWalletExport())
        self.register_sub_command(CommandWalletImport())
        self.register_sub_command(CommandWalletAddress())

    def command_desc(self):
        return CommandDesc('wallet', 'manage wallets')

    def execute(self, arguments):
        wallet = PromptData.Wallet
        item = PromptUtils.get_arg(arguments)

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

    def _usage_str(self):
        base = super()._usage_str()
        return base + " (or \"wallet\" to show the wallet contents)"


class CommandWalletCreate(CommandBase):

    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        path = PromptUtils.get_arg(arguments, 0)

        if not path:
            print("Please specify a path")
            return

        if os.path.exists(path):
            print("File already exists")
            return

        if PromptData.Wallet:
            PromptData.close_wallet()

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

        path = PromptUtils.get_arg(arguments, 0)

        if not path:
            print("Please specify the required parameter")
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


class CommandWalletClaimGas(CommandBase):

    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        from_addr_str = None
        to_addr_str = None

        args = arguments
        if args:
            args, from_addr_str = PromptUtils.get_from_addr(args)
            args, to_addr_str = PromptUtils.get_to_addr(args)

        return ClaimGas(PromptData.Wallet, True, from_addr_str, to_addr_str)

    def command_desc(self):
        p1 = ParameterDesc('--from-addr', 'source address to claim gas from (if not specified, take first address in wallet)', optional=True)
        p2 = ParameterDesc('--to-addr', 'destination address for claimed gas (if not specified, take first address in wallet; or, use the from address, if specified)', optional=True)
        return CommandDesc('claim', 'claim gas', params=[p1, p2])


class CommandWalletRebuild(CommandBase):

    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        PromptData.Prompt.stop_wallet_loop()

        start_block = PromptUtils.get_arg(arguments, 0, convert_to_int=True)
        if not start_block or start_block < 0:
            start_block = 0
        print(f"Restarting at block {start_block}")

        PromptData.Wallet.Rebuild(start_block)

        PromptData.Prompt.start_wallet_loop()

    def command_desc(self):
        p1 = ParameterDesc('start_block', 'block number to start the resync at', optional=True)
        return CommandDesc('rebuild', 'rebuild the wallet index', params=[p1])


class CommandWalletUnspent(CommandBase):

    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        asset_id = None
        from_addr = None
        watch_only = False
        do_count = False
        wallet = PromptData.Wallet

        arguments, from_addr_str = PromptUtils.get_from_addr(arguments)
        if from_addr_str:
            if not isValidPublicAddress(from_addr_str):
                print("Invalid address specified")
                return

            from_addr = wallet.ToScriptHash(from_addr_str)

        for item in arguments:
            if item == '--watch':
                watch_only = True
            elif item == '--count':
                do_count = True
            else:
                asset_id = PromptUtils.get_asset_id(wallet, item)

        return ShowUnspentCoins(wallet, asset_id, from_addr, watch_only, do_count)

    def command_desc(self):
        p1 = ParameterDesc('asset', 'type of asset to query (NEO/GAS)', optional=True)
        p2 = ParameterDesc('--from-addr', 'address to check the unspent assets from (if not specified, checks for all addresses)', optional=True)
        p3 = ParameterDesc('--watch', 'show assets that are in watch only addresses', optional=True)
        p4 = ParameterDesc('--count', 'only count the unspent assets', optional=True)
        return CommandDesc('unspent', 'show unspent assets', params=[p1, p2, p3, p4])


#########################################################################
#########################################################################


def ClaimGas(wallet, require_password=True, from_addr_str=None, to_addr_str=None):
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
        print("No claims to process")
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
        script_hash = None
        script_hash = PromptUtils.lookup_addr_str(wallet, from_addr_str)
        if script_hash is None:
            logger.debug("invalid source address")
            return None, False
        standard_contract = wallet.GetStandardAddress()
        claim_tx.Attributes = [TransactionAttribute(usage=TransactionAttributeUsage.Script,
                                                    data=standard_contract.Data)]

    if to_addr_str:
        script_hash = None
        script_hash = PromptUtils.lookup_addr_str(wallet, to_addr_str)
        if script_hash is None:
            logger.debug("invalid destination address")
            return None, False

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
            print("Incorrect password")
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


def ShowUnspentCoins(wallet, asset_id=None, from_addr=None, watch_only=False, do_count=False):
    """
    Show unspent coin objects in the wallet.

    Args:
        wallet (neo.Wallet): wallet to show unspent coins from.
        asset_id (UInt256): a bytearray (len 32) representing an asset on the blockchain.
        from_addr (UInt160): a bytearray (len 20) representing an address.
        watch_only (bool): indicate if this shows coins that are in 'watch only' addresses.
        do_count (bool): if True only show a count of unspent assets.

    Returns:
        list: a list of unspent ``neo.Wallet.Coin`` in the wallet
    """

    if wallet is None:
        print("Please open a wallet.")
        return

    watch_only_flag = 64 if watch_only else 0
    if asset_id:
        unspents = wallet.FindUnspentCoinsByAsset(asset_id, from_addr=from_addr, watch_only_val=watch_only_flag)
    else:
        unspents = wallet.FindUnspentCoins(from_addr=from_addr, watch_only_val=watch_only)

    if do_count:
        print('\n-----------------------------------------------')
        print('Total Unspent: %s' % len(unspents))
        return unspents

    for unspent in unspents:
        print('\n-----------------------------------------------')
        print(json.dumps(unspent.ToJson(), indent=4))

    if not unspents:
        print("No unspent assets matching the arguments.")

    return unspents
