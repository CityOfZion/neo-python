from neo.Prompt.Commands.Invoke import InvokeContract, InvokeWithTokenVerificationScript
from neo.Prompt.Utils import get_asset_id, get_from_addr, get_tx_attr_from_args
from neo.Wallets.NEP5Token import NEP5Token
from neocore.Fixed8 import Fixed8
from prompt_toolkit import prompt
from decimal import Decimal


def token_send(wallet, args, prompt_passwd=True):
    if len(args) != 4:
        print("please provide a token symbol, from address, to address, and amount")
        return False

    token = get_asset_id(wallet, args[0])
    send_from = args[1]
    send_to = args[2]
    amount = amount_from_string(token, args[3])

    return do_token_transfer(token, wallet, send_from, send_to, amount, prompt_passwd=prompt_passwd)


def token_send_from(wallet, args, prompt_passwd=True):
    if len(args) != 4:
        print("please provide a token symbol, from address, to address, and amount")
        return False

    token = get_asset_id(wallet, args[0])
    send_from = args[1]
    send_to = args[2]
    amount = amount_from_string(token, args[3])

    allowance = token_get_allowance(wallet, args[:-1], verbose=False)

    if allowance and allowance >= amount:

        tx, fee, results = token.TransferFrom(wallet, send_from, send_to, amount)

        if tx is not None and results is not None and len(results) > 0:

            if results[0].GetBigInteger() == 1:

                if prompt_passwd:

                    print("\n-----------------------------------------------------------")
                    print("Transfer of %s %s from %s to %s" % (
                        string_from_amount(token, amount), token.symbol, send_from, send_to))
                    print("Transfer fee: %s " % (fee.value / Fixed8.D))
                    print("-------------------------------------------------------------\n")

                    passwd = prompt("[Password]> ", is_password=True)

                    if not wallet.ValidatePassword(passwd):
                        print("incorrect password")
                        return False

                return InvokeContract(wallet, tx, fee)

    print("Requested transfer from is greater than allowance")

    return False


def token_approve_allowance(wallet, args, prompt_passwd=True):
    if len(args) != 4:
        print("please provide a token symbol, from address, to address, and amount")
        return False

    token = get_asset_id(wallet, args[0])
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
                    return

            return InvokeContract(wallet, tx, fee)

    print("could not transfer tokens")
    return False


def token_get_allowance(wallet, args, verbose=False):
    if len(args) != 3:
        print("please provide a token symbol, from address, to address")
        return

    token = get_asset_id(wallet, args[0])
    allowance_from = args[1]
    allowance_to = args[2]

    tx, fee, results = token.Allowance(wallet, allowance_from, allowance_to)

    if tx is not None and results is not None and len(results) > 0:
        allowance = results[0].GetBigInteger()
        if verbose:
            print("%s allowance for %s from %s : %s " % (token.symbol, allowance_to, allowance_from, allowance))

        return allowance
    else:
        if verbose:
            print("Could not get allowance for token %s " % token.symbol)

    return 0


def token_mint(wallet, args, prompt_passwd=True):
    token = get_asset_id(wallet, args[0])
    mint_to_addr = args[1]
    args, invoke_attrs = get_tx_attr_from_args(args)
    if len(args) < 3:
        raise Exception("please specify assets to attach")

    asset_attachments = args[2:]

    tx, fee, results = token.Mint(wallet, mint_to_addr, asset_attachments, invoke_attrs=invoke_attrs)

    if results[0] is not None:
        print("\n-----------------------------------------------------------")
        print("[%s] Will mint tokens to address: %s " % (token.symbol, mint_to_addr))
        print("Fee: %s " % (fee.value / Fixed8.D))
        print("-------------------------------------------------------------\n")

        if prompt_passwd:
            passwd = prompt("[Password]> ", is_password=True)

            if not wallet.ValidatePassword(passwd):
                print("incorrect password")
                return

        return InvokeWithTokenVerificationScript(wallet, tx, token, fee, invoke_attrs=invoke_attrs)

    else:
        print("Could not register addresses: %s " % str(results[0]))

    return False


def token_crowdsale_register(wallet, args, prompt_passwd=True):
    token = get_asset_id(wallet, args[0])

    args, from_addr = get_from_addr(args)

    if len(args) < 2:
        raise Exception("Specify addr to register for crowdsale")
    register_addr = args[1:]

    tx, fee, results = token.CrowdsaleRegister(wallet, register_addr)

    if results[0].GetBigInteger() > 0:
        print("\n-----------------------------------------------------------")
        print("[%s] Will register addresses for crowdsale: %s " % (token.symbol, register_addr))
        print("Fee: %s " % (fee.value / Fixed8.D))
        print("-------------------------------------------------------------\n")

        if prompt_passwd:
            passwd = prompt("[Password]> ", is_password=True)

            if not wallet.ValidatePassword(passwd):
                print("incorrect password")
                return

        return InvokeContract(wallet, tx, fee, from_addr)

    else:
        print("Could not register addresses: %s " % str(results[0]))

    return False


def do_token_transfer(token, wallet, from_address, to_address, amount, prompt_passwd=True):
    if from_address is None:
        print("Please specify --from-addr={addr} to send NEP5 tokens")
        return False

    tx, fee, results = token.Transfer(wallet, from_address, to_address, amount)

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


def token_history(wallet, db, args):
    if len(args) < 1:
        print("Please provide the token symbol of the token you wish consult")
        return False

    if not db:
        print("Unable to fetch history, notification database not enabled")
        return False

    token = get_asset_id(wallet, args[0])

    if not isinstance(token, NEP5Token):
        print("The given symbol does not represent a loaded NEP5 token")
        return False

    events = db.get_by_contract(token.ScriptHash)

    addresses = wallet.Addresses
    print("-----------------------------------------------------------")
    print("Recent transaction history (last = more recent):")
    for event in events:
        if event.Type != 'transfer':
            continue
        if event.AddressFrom in addresses:
            print(f"[{event.AddressFrom}]: Sent {string_from_amount(token, event.Amount)}"
                  f" {args[0]} to {event.AddressTo}")
        if event.AddressTo in addresses:
            print(f"[{event.AddressTo}]: Received {string_from_amount(token, event.Amount)}"
                  f" {args[0]} from {event.AddressFrom}")
    print("-----------------------------------------------------------")
    return True


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
