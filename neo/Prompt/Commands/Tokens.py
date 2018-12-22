from neo.Prompt.Commands.Invoke import InvokeContract, InvokeWithTokenVerificationScript
from neo.Wallets.NEP5Token import NEP5Token
from neocore.Fixed8 import Fixed8
from neocore.UInt160 import UInt160
from prompt_toolkit import prompt
from decimal import Decimal
from neo.Core.TX.TransactionAttribute import TransactionAttribute
import binascii
from neo.Prompt.CommandBase import CommandBase, CommandDesc, ParameterDesc
from neo.Prompt.PromptData import PromptData
from neo.Prompt import Utils as PromptUtils
from neo.Implementations.Wallets.peewee.Models import NEP5Token as ModelNEP5Token
from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB
from neo.Core.TX.TransactionAttribute import TransactionAttributeUsage
from neocore.Utils import isValidPublicAddress
from distutils.util import strtobool
import peewee
import traceback

from neo.logging import log_manager

logger = log_manager.getLogger()


class CommandWalletToken(CommandBase):
    def __init__(self):
        super().__init__()
        self.register_sub_command(CommandTokenDelete())
        self.register_sub_command(CommandTokenSend())
        self.register_sub_command(CommandTokenSendFrom())
        self.register_sub_command(CommandTokenHistory())

    def command_desc(self):
        return CommandDesc('token', 'various token operations')

    def execute(self, arguments):
        item = PromptUtils.get_arg(arguments)

        if not item:
            print(f"Please specify an action. See help for available actions")
            return False

        try:
            return self.execute_sub_command(item, arguments[1:])
        except KeyError:
            print(f"{item} is an invalid parameter")
            return False


class CommandTokenDelete(CommandBase):

    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        wallet = PromptData.Wallet

        if len(arguments) != 1:
            print("Please specify the required parameter")
            return False

        hash_string = arguments[0]
        try:
            script_hash = UInt160.ParseString(hash_string)
        except Exception:
            # because UInt160 throws a generic exception. Should be fixed in the future
            print("Invalid script hash")
            return False

        # try to find token and collect some data
        try:
            token = ModelNEP5Token.get(ContractHash=script_hash)
        except peewee.DoesNotExist:
            print(f"Could not find a token with script_hash {arguments[0]}")
            return False

        success = wallet.DeleteNEP5Token(script_hash)
        if success:
            print(f"Token {token.Symbol} with script_hash {arguments[0]} deleted")
        else:
            # probably unreachable to due token check earlier. Better safe than sorrow
            print(f"Could not find a token with script_hash {arguments[0]}")

        return success

    def command_desc(self):
        p1 = ParameterDesc('contract', 'token contract hash (script_hash)')
        return CommandDesc('delete', 'remove a token from the wallet', [p1])


class CommandTokenSend(CommandBase):

    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        wallet = PromptData.Wallet

        if len(arguments) < 4:
            print("Please specify the required parameters")
            return False

        if len(arguments) > 5:
            # the 5th argument is the optional attributes,
            print("Too many parameters supplied. Please check your command")
            return False

        _, user_tx_attributes = PromptUtils.get_tx_attr_from_args(arguments)

        token = arguments[0]
        from_addr = arguments[1]
        to_addr = arguments[2]
        try:
            amount = float(arguments[3])
        except ValueError:
            print(f"{arguments[3]} is not a valid amount")
            return False

        try:
            success = token_send(wallet, token, from_addr, to_addr, amount, user_tx_attributes)
        except ValueError as e:
            # occurs if arguments are invalid
            print(str(e))
            success = False

        return success

    def command_desc(self):
        p1 = ParameterDesc('token', 'token symbol name or script_hash')
        p2 = ParameterDesc('from_addr', 'address to send token from')
        p3 = ParameterDesc('to_addr', 'address to send token to')
        p4 = ParameterDesc('amount', 'number of tokens to send')
        p5 = ParameterDesc('--tx-attr', f"a list of transaction attributes to attach to the transaction\n\n"
        f"{' ':>17} See: http://docs.neo.org/en-us/network/network-protocol.html section 4 for a description of possible attributes\n\n"  # noqa: E128 ignore indentation
        f"{' ':>17} Example:\n"
        f"{' ':>20} --tx-attr=[{{\"usage\": <value>,\"data\":\"<remark>\"}}, ...]\n"
        f"{' ':>20} --tx-attr=[{{\"usage\": 0x90,\"data\":\"my brief description\"}}]\n", optional=True)

        return CommandDesc('send', 'send a token from the wallet', [p1, p2, p3, p4, p5])


class CommandTokenSendFrom(CommandBase):
    """
    This command is for old style NEP-5 tokens before the proposal got amended to remove this optional command.
    """

    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        wallet = PromptData.Wallet

        if len(arguments) < 4:
            print("Please specify the required parameters")
            return False

        if len(arguments) > 5:
            # the 5th argument is prompting for a password before sending,
            print("Too many parameters supplied. Please check your command")
            return False

        token_str = arguments[0]
        from_addr = arguments[1]
        to_addr = arguments[2]

        try:
            amount = float(arguments[3])
        except ValueError:
            print(f"{arguments[3]} is not a valid amount")
            return False

        prompt_passwd = True
        if len(arguments) == 5:
            try:
                prompt_passwd = bool(strtobool(arguments[4]))
            except ValueError:
                print("Invalid value for showing prompt parameter. Must be True or False if supplied")
                return False

        try:
            token, tx, fee, results = test_token_send_from(wallet, token_str, from_addr, to_addr, amount)
        except ValueError as e:
            # invalid arguments or bad allowance
            print(str(e))
            return False
        except Exception as e:
            # we act as the final capturing place
            print("Something really unexpected happened")
            logger.error(traceback.format_exc())
            return False

        if tx and results and len(results) > 0:
            vm_result = results[0].GetBigInteger()
            if vm_result == 1:
                print("\n-----------------------------------------------------------")
                print("Transfer of %s %s from %s to %s" % (
                    string_from_amount(token, amount), token.symbol, from_addr, to_addr))
                print("Transfer fee: %s " % (fee.value / Fixed8.D))
                print("-------------------------------------------------------------\n")

                if prompt_passwd:
                    passwd = prompt("[Password]> ", is_password=True)

                    if not wallet.ValidatePassword(passwd):
                        print("incorrect password")
                        return False

                return InvokeContract(wallet, tx, fee)

            print(f"Could not transfer tokens. Virtual machine returned: {vm_result}")
            return False

        print(f"Could not transfer tokens. An unknown error occurred resulting in no Transaction object or VM output.")
        return False

    def command_desc(self):
        p1 = ParameterDesc('token', 'token symbol name or script_hash')
        p2 = ParameterDesc('from_addr', 'address to send token from')
        p3 = ParameterDesc('to_addr', 'address to send token to')
        p4 = ParameterDesc('amount', 'number of tokens to send')
        p5 = ParameterDesc('ask_for_passw', 'prompt for a password before sending to the actual network. Default is True', optional=True)

        return CommandDesc('sendfrom', 'send a token on behalf of another account (requires approval)', [p1, p2, p3, p4, p5])


class CommandTokenHistory(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        wallet = PromptData.Wallet

        if len(arguments) != 1:
            print("Please specify the required parameter")
            return False

        try:
            token, events = token_history(wallet, arguments[0])
        except ValueError as e:
            print(str(e))
            return False

        if events:
            addresses = wallet.Addresses
            print("-----------------------------------------------------------")
            print("Recent transaction history (last = more recent):")
            for event in events:
                if event.Type != 'transfer':
                    continue
                if event.AddressFrom in addresses:
                    print(f"[{event.AddressFrom}]: Sent {string_from_amount(token, event.Amount)}"
                          f" {token.symbol} to {event.AddressTo}")
                if event.AddressTo in addresses:
                    print(f"[{event.AddressTo}]: Received {string_from_amount(token, event.Amount)}"
                          f" {token.symbol} from {event.AddressFrom}")
            print("-----------------------------------------------------------")
        else:
            print("History contains no transactions")
        return True

    def command_desc(self):
        p1 = ParameterDesc('symbol', 'token symbol')
        return CommandDesc('history', 'show transaction history', [p1])


def _validate_nep5_args(wallet, token_str, from_addr, to_addr, amount):
    """
    A helper function to validate common arguments used in NEP-5 functions

    Args:
        wallet (Wallet): a UserWallet instance
        token_str (str): symbol name or script_hash
        from_addr (str): a wallet address
        to_addr (str): a wallet address
        amount (float): the number of tokens to send

    Raises:
        ValueError: for invalid arguments

    Returns:
        token (NEP5Token): instance
    """
    token = None
    for t in wallet.GetTokens().values():
        if token_str == t.symbol:
            token = t
            break
        elif token_str == t.ScriptHash.ToString():
            token = t

    if not isinstance(token, NEP5Token):
        raise ValueError("The given token argument does not represent a known NEP5 token")

    if not isValidPublicAddress(from_addr):
        raise ValueError("send_from is not a valid address")

    if not isValidPublicAddress(to_addr):
        raise ValueError("send_to is not a valid address")

    try:
        # internally this function uses the `Decimal` class which will parse the float amount to its required format.
        # the name is a bit misleading /shrug
        amount = amount_from_string(token, amount)
    except Exception:
        raise ValueError(f"{amount} is not a valid amount")

    return token


def token_send(wallet, token_str, from_addr, to_addr, amount, prompt_passwd=True, user_tx_attributes=None):
    """
    Send `amount` of tokens from `from_addr` to `to_addr`

    Args:
        wallet (Wallet): a UserWallet instance
        token_str (str): symbol name or script_hash
        from_addr (str): a wallet address
        to_addr (str): a wallet address
        amount (float): the number of tokens to send
        prompt_passwd (boolean): (optional) whether to prompt for a password before sending it to the network. Defaults to True
        user_tx_attributes (list): a list of ``TransactionAttribute``s.

    Raises:
        ValueError: for invalid arguments

    Returns:
        a Transaction object if successful, False otherwise.
    """
    if not user_tx_attributes:
        user_tx_attributes = []

    try:
        token = _validate_nep5_args(wallet, token_str, from_addr, to_addr, amount)
    except ValueError:
        # just making it explicit for the reader
        raise

    for attr in user_tx_attributes:
        if not isinstance(attr, TransactionAttribute):
            raise ValueError(f"{attr} is not a valid transaction attribute")

    return do_token_transfer(token, wallet, from_addr, to_addr, amount, prompt_passwd=prompt_passwd, tx_attributes=user_tx_attributes)


def test_token_send_from(wallet, token_str, from_addr, to_addr, amount):
    """
    Test sending funds from `addr_from` to `addr_to` without commiting to the network.

    This does a local test to validate all supplied arguments and if the blockchain state allows for the transfer.

    Args:
        wallet (Wallet): a UserWallet instance
        token_str (str): symbol name or script_hash
        from_addr (str): a wallet address
        to_addr (str): a wallet address
        amount (float): the number of tokens to send

    Raises:
        ValueError: for invalid arguments or if allowance is insufficient.

    Returns:
        tuple:
            token (NEP5Token): instance
            InvocationTransaction: the transaction.
            int: the transaction fee.
            list: the neo VM evaluation stack results.
    """
    try:
        token = _validate_nep5_args(wallet, token_str, from_addr, to_addr, amount)
        allowance = token_get_allowance(wallet, token_str, from_addr, to_addr, verbose=False)

        if allowance < amount:
            raise ValueError(f"Insufficient allowance: {allowance}")
    except ValueError:
        # bad args or allowance
        raise

    tx, fees, results = token.TransferFrom(wallet, from_addr, to_addr, amount)
    return token, tx, fees, results


def token_approve_allowance(wallet, args, prompt_passwd=True):
    if len(args) != 4:
        print("please provide a token symbol, from address, to address, and amount")
        return False

    token = PromptUtils.get_asset_id(wallet, args[0])
    if not isinstance(token, NEP5Token):
        print("The given symbol does not represent a loaded NEP5 token")
        return False

    approve_from = args[1]
    approve_to = args[2]
    amount = amount_from_string(token, args[3])

    tx, fee, results = token.Approve(wallet, approve_from, approve_to, amount)

    if tx is not None and results is not None and len(results) > 0:
        if results[0].GetBigInteger() == 1:
            print("\n-----------------------------------------------------------")
            print("Approve allowance of %s %s from %s to %s" % (string_from_amount(token, amount), token.symbol, approve_from, approve_to))
            print("Transfer fee: %s " % (fee.value / Fixed8.D))
            print("-------------------------------------------------------------\n")

            if prompt_passwd:
                passwd = prompt("[Password]> ", is_password=True)

                if not wallet.ValidatePassword(passwd):
                    print("incorrect password")
                    return False

            return InvokeContract(wallet, tx, fee)

    print("could not transfer tokens")
    return False


def token_get_allowance(wallet, token_str, from_addr, to_addr, verbose=False):
    """
    Query the smart contract for the amount from_addr is allowed to send to to_addr

    Requires amount to be `approved`.

    Args:
        wallet (Wallet): a UserWallet instance
        token_str (str): symbol name or script_hash
        from_addr (str): a wallet address
        to_addr (str): a wallet address
        verbose (bool): flag indicating whether to print VM results

    Raises:
        ValueError: for invalid arguments or if allowance could not be queried

    Returns:
        int: allowance
    """
    try:
        token = _validate_nep5_args(wallet, token_str, from_addr, to_addr, amount=0)
    except ValueError:
        raise

    tx, fee, results = token.Allowance(wallet, from_addr, to_addr)

    if tx and results and len(results) > 0:
        allowance = results[0].GetBigInteger()
        if verbose:
            print("%s allowance for %s from %s : %s " % (token.symbol, from_addr, to_addr, allowance))

        return allowance
    else:
        if verbose:
            print("Could not get allowance for token %s " % token.symbol)
        raise ValueError(f"Could not get allowance for token {token.symbol}")


def token_mint(wallet, args, prompt_passwd=True):
    token = PromptUtils.get_asset_id(wallet, args[0])
    if not isinstance(token, NEP5Token):
        print("The given symbol does not represent a loaded NEP5 token")
        return False

    mint_to_addr = args[1]
    args, invoke_attrs = PromptUtils.get_tx_attr_from_args(args)
    if len(args) < 3:
        print("please specify assets to attach")
        return False

    asset_attachments = args[2:]

    tx, fee, results = token.Mint(wallet, mint_to_addr, asset_attachments, invoke_attrs=invoke_attrs)

    if tx is not None and results is not None and len(results) > 0:
        if results[0] is not None:
            print("\n-----------------------------------------------------------")
            print("[%s] Will mint tokens to address: %s " % (token.symbol, mint_to_addr))
            print("Fee: %s " % (fee.value / Fixed8.D))
            print("-------------------------------------------------------------\n")

            if prompt_passwd:
                passwd = prompt("[Password]> ", is_password=True)

                if not wallet.ValidatePassword(passwd):
                    print("incorrect password")
                    return False

            return InvokeWithTokenVerificationScript(wallet, tx, token, fee, invoke_attrs=invoke_attrs)

    print("Could not register address")
    return False


def token_crowdsale_register(wallet, args, prompt_passwd=True):
    token = PromptUtils.get_asset_id(wallet, args[0])
    if not isinstance(token, NEP5Token):
        print("The given symbol does not represent a loaded NEP5 token")
        return False

    args, from_addr = PromptUtils.get_from_addr(args)

    if len(args) < 2:
        print("Specify addr to register for crowdsale")
        return False

    register_addr = args[1:]

    tx, fee, results = token.CrowdsaleRegister(wallet, register_addr)

    if tx is not None and results is not None and len(results) > 0:
        if results[0].GetBigInteger() > 0:
            print("\n-----------------------------------------------------------")
            print("[%s] Will register addresses for crowdsale: %s " % (token.symbol, register_addr))
            print("Fee: %s " % (fee.value / Fixed8.D))
            print("-------------------------------------------------------------\n")

            if prompt_passwd:
                passwd = prompt("[Password]> ", is_password=True)

                if not wallet.ValidatePassword(passwd):
                    print("incorrect password")
                    return False

            return InvokeContract(wallet, tx, fee, from_addr)

    print("Could not register address(es)")
    return False


def do_token_transfer(token, wallet, from_address, to_address, amount, prompt_passwd=True, tx_attributes=None):
    if not tx_attributes:
        tx_attributes = []

    # because we cannot differentiate between a normal and multisig from_addr, and because we want to make
    # sending NEP5 tokens straight forward even when sending from multisig addresses, we include the script_hash
    # for verification by default to the transaction attributes. See PR/Issue: https://github.com/CityOfZion/neo-python/pull/491
    from_script_hash = binascii.unhexlify(bytes(wallet.ToScriptHash(from_address).ToString2(), 'utf-8'))
    tx_attributes.append(TransactionAttribute(usage=TransactionAttributeUsage.Script, data=from_script_hash))

    tx, fee, results = token.Transfer(wallet, from_address, to_address, amount, tx_attributes=tx_attributes)

    if tx is not None and results is not None and len(results) > 0:

        if results[0].GetBigInteger() == 1:
            print("\n-----------------------------------------------------------")
            print("Will transfer %s %s from %s to %s" % (string_from_amount(token, amount), token.symbol, from_address, to_address))
            print("Transfer fee: %s " % (fee.value / Fixed8.D))
            print("-------------------------------------------------------------\n")

            if prompt_passwd:
                passwd = prompt("[Password]> ", is_password=True)

                if not wallet.ValidatePassword(passwd):
                    print("incorrect password")
                    return False

            return InvokeContract(wallet, tx, fee)

    print("could not transfer tokens")
    return False


def token_history(wallet, token_str):
    notification_db = NotificationDB.instance()

    try:
        token = PromptUtils.get_token(wallet, token_str)
    except ValueError:
        raise

    events = notification_db.get_by_contract(token.ScriptHash)
    return token, events


def amount_from_string(token, amount_str):
    precision_mult = pow(10, token.decimals)
    amount = Decimal(amount_str) * precision_mult

    return int(amount)


def string_from_amount(token, amount):
    precision_mult = pow(10, token.decimals)
    amount = Decimal(amount) / Decimal(precision_mult)
    formatter_str = '.%sf' % token.decimals
    amount_str = format(amount, formatter_str)

    return amount_str
