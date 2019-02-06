from neo.Core.TX.Transaction import TransactionOutput, ContractTransaction, TXFeeError
from neo.Core.TX.TransactionAttribute import TransactionAttribute, TransactionAttributeUsage
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neo.Network.NodeLeader import NodeLeader
from neo.Prompt.Utils import get_arg, get_from_addr, get_asset_id, lookup_addr_str, get_tx_attr_from_args, \
    get_owners_from_params, get_fee, get_change_addr, get_asset_amount
from neo.Prompt.Commands.Tokens import do_token_transfer, amount_from_string
from neo.Prompt.Commands.Invoke import gather_signatures
from neo.Wallets.NEP5Token import NEP5Token
from neocore.Fixed8 import Fixed8
import json
from prompt_toolkit import prompt
import traceback
from neo.Prompt.PromptData import PromptData
from neo.Prompt.CommandBase import CommandBase, CommandDesc, ParameterDesc
from logzero import logger
from neo.Prompt.PromptPrinter import prompt_print as print
from neo.Core.Blockchain import Blockchain


class CommandWalletSend(CommandBase):

    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        framework = construct_send_basic(PromptData.Wallet, arguments)

        if type(framework) is list:
            # if no `--from-addr` is specified, then make sure we take the first address that is shown when using `wallet`
            funds_source_script_hash = framework[1]
            if not funds_source_script_hash:
                funds_source_script_hash = PromptData.Wallet.ToScriptHash(PromptData.Wallet.Addresses[0])

            return process_transaction(PromptData.Wallet, contract_tx=framework[0], scripthash_from=funds_source_script_hash,
                                       fee=framework[2], owners=framework[3], user_tx_attributes=framework[4])
        return framework

    def command_desc(self):
        p1 = ParameterDesc('asset', 'assetId or name (NEO/GAS) to send')
        p2 = ParameterDesc('address', 'destination address')
        p3 = ParameterDesc('amount', 'amount of the asset to send')
        p4 = ParameterDesc('--from-addr', 'source address to take funds from (if not specified, take first address in wallet)', optional=True)
        p5 = ParameterDesc('--fee', 'Attach GAS amount to give your transaction priority (> 0.001) e.g. --fee=0.01', optional=True)
        p6 = ParameterDesc('--owners', 'list of NEO addresses indicating the transaction owners e.g. --owners=[address1,address2]', optional=True)
        p7 = ParameterDesc('--tx-attr',
                           f"list of transaction attributes to attach to the transaction\n\n"
                           f"{' ':>17} See: http://docs.neo.org/en-us/network/network-protocol.html section 4 for a description of possible attributes\n\n"
                           f"{' ':>17} Example:\n"
                           f"{' ':>20} --tx-attr=[{{\"usage\": <value>,\"data\":\"<remark>\"}}, ...]\n"
                           f"{' ':>20} --tx-attr=[{{\"usage\": 0x90,\"data\":\"my brief description\"}}]\n", optional=True)
        params = [p1, p2, p3, p4, p5, p6, p7]
        return CommandDesc('send', 'send an asset (NEO/GAS)', params=params)


class CommandWalletSendMany(CommandBase):

    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        framework = construct_send_many(PromptData.Wallet, arguments)

        if type(framework) is list:
            # if no `--from-addr` is specified, then make sure we take the first address that is shown when using `wallet`
            funds_source_script_hash = framework[1]
            if not funds_source_script_hash:
                funds_source_script_hash = PromptData.Wallet.ToScriptHash(PromptData.Wallet.Addresses[0])

            return process_transaction(PromptData.Wallet, contract_tx=framework[0], scripthash_from=funds_source_script_hash, scripthash_change=framework[2],
                                       fee=framework[3], owners=framework[4], user_tx_attributes=framework[5])
        return framework

    def command_desc(self):
        p1 = ParameterDesc('tx_count', 'number of transactions to send')
        p2 = ParameterDesc('--change-addr', 'address to send remaining funds to', optional=True)
        p3 = ParameterDesc('--from-addr', 'source address to take funds from (if not specified, take first address in wallet)', optional=True)
        p4 = ParameterDesc('--fee', 'Attach GAS amount to give your transaction priority (> 0.001) e.g. --fee=0.01', optional=True)
        p5 = ParameterDesc('--owners', 'list of NEO addresses indicating the transaction owners e.g. --owners=[address1,address2]', optional=True)
        p6 = ParameterDesc('--tx-attr',
                           f"a list of transaction attributes to attach to the transaction\n\n"
                           f"{' ':>17} See: http://docs.neo.org/en-us/network/network-protocol.html section 4 for a description of possible attributes\n\n"
                           f"{' ':>17} Example:\n"
                           f"{' ':>20} --tx-attr=[{{\"usage\": <value>,\"data\":\"<remark>\"}}, ...]\n"
                           f"{' ':>20} --tx-attr=[{{\"usage\": 0x90,\"data\":\"my brief description\"}}]\n", optional=True)
        params = [p1, p2, p3, p4, p5, p6]
        return CommandDesc('sendmany', 'send multiple NEO/GAS transactions', params=params)


class CommandWalletSign(CommandBase):

    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        jsn = get_arg(arguments)
        if not jsn:
            print("Please specify the required parameter")
            return False

        return parse_and_sign(PromptData.Wallet, jsn)

    def command_desc(self):
        p1 = ParameterDesc('jsn', 'transaction in JSON format')
        params = [p1]
        return CommandDesc('sign', 'sign a multi-signature transaction', params=params)


def construct_send_basic(wallet, arguments):
    if len(arguments) < 3:
        print("Please specify the required parameters")
        return

    arguments, from_address = get_from_addr(arguments)
    arguments, priority_fee = get_fee(arguments)
    arguments, user_tx_attributes = get_tx_attr_from_args(arguments)
    arguments, owners = get_owners_from_params(arguments)
    to_send = get_arg(arguments)
    address_to = get_arg(arguments, 1)
    amount = get_arg(arguments, 2)

    assetId = get_asset_id(wallet, to_send)
    if assetId is None:
        print("Asset id not found")
        return

    scripthash_to = lookup_addr_str(wallet, address_to)
    if scripthash_to is None:
        logger.debug("invalid destination address")
        return

    scripthash_from = None
    if from_address is not None:
        scripthash_from = lookup_addr_str(wallet, from_address)
        if scripthash_from is None:
            logger.debug("invalid source address")
            return

    # if this is a token, we will use a different
    # transfer mechanism
    if type(assetId) is NEP5Token:
        return do_token_transfer(assetId, wallet, from_address, address_to, amount_from_string(assetId, amount),
                                 tx_attributes=user_tx_attributes)

    f8amount = get_asset_amount(amount, assetId)
    if f8amount is False:
        logger.debug("invalid amount")
        return
    if float(amount) == 0:
        print("Amount cannot be 0")
        return

    fee = Fixed8.Zero()
    if priority_fee is not None:
        fee = priority_fee
        if fee is False:
            logger.debug("invalid fee")
            return
    print(f"Sending with fee: {fee.ToString()}")

    output = TransactionOutput(AssetId=assetId, Value=f8amount, script_hash=scripthash_to)
    contract_tx = ContractTransaction(outputs=[output])
    return [contract_tx, scripthash_from, fee, owners, user_tx_attributes]


def construct_send_many(wallet, arguments):
    if len(arguments) is 0:
        print("Please specify the required parameter")
        return

    outgoing = get_arg(arguments, convert_to_int=True)
    if outgoing is None:
        print("Invalid outgoing number")
        return
    if outgoing < 1:
        print("Outgoing number must be >= 1")
        return

    arguments, from_address = get_from_addr(arguments)
    arguments, change_address = get_change_addr(arguments)
    arguments, priority_fee = get_fee(arguments)
    arguments, owners = get_owners_from_params(arguments)
    arguments, user_tx_attributes = get_tx_attr_from_args(arguments)

    output = []
    for i in range(outgoing):
        try:
            print('Outgoing Number ', i + 1)
            to_send = prompt("Asset to send: ")
            assetId = get_asset_id(wallet, to_send)
            if assetId is None:
                print("Asset id not found")
                return
            if type(assetId) is NEP5Token:
                print('sendmany does not support NEP5 tokens')
                return
            address_to = prompt("Address to: ")
            scripthash_to = lookup_addr_str(wallet, address_to)
            if scripthash_to is None:
                logger.debug("invalid destination address")
                return
            amount = prompt("Amount to send: ")
            f8amount = get_asset_amount(amount, assetId)
            if f8amount is False:
                logger.debug("invalid amount")
                return
            if float(amount) == 0:
                print("Amount cannot be 0")
                return
            tx_output = TransactionOutput(AssetId=assetId, Value=f8amount, script_hash=scripthash_to)
            output.append(tx_output)
        except KeyboardInterrupt:
            print('Transaction cancelled')
            return
    contract_tx = ContractTransaction(outputs=output)

    scripthash_from = None

    if from_address is not None:
        scripthash_from = lookup_addr_str(wallet, from_address)
        if scripthash_from is None:
            logger.debug("invalid source address")
            return

    scripthash_change = None

    if change_address is not None:
        scripthash_change = lookup_addr_str(wallet, change_address)
        if scripthash_change is None:
            logger.debug("invalid change address")
            return

    fee = Fixed8.Zero()
    if priority_fee is not None:
        fee = priority_fee
        if fee is False:
            logger.debug("invalid fee")
            return

    print(f"Sending with fee: {fee.ToString()}")
    return [contract_tx, scripthash_from, scripthash_change, fee, owners, user_tx_attributes]


def process_transaction(wallet, contract_tx, scripthash_from=None, scripthash_change=None, fee=None, owners=None, user_tx_attributes=None):
    try:
        tx = wallet.MakeTransaction(tx=contract_tx,
                                    change_address=scripthash_change,
                                    fee=fee,
                                    from_addr=scripthash_from)
    except ValueError:
        print("Insufficient funds. No unspent outputs available for building the transaction.\n"
              "If you are trying to sent multiple transactions in 1 block, then make sure you have enough 'vouts'\n."
              "Use `wallet unspent` and `wallet address split`, or wait until the first transaction is processed before sending another.")
        return
    except TXFeeError as e:
        print(e)
        return

    if tx is None:
        logger.debug("insufficient funds")
        return

    try:
        print("Validate your transaction details")
        print("-" * 33)
        input_coinref = wallet.FindCoinsByVins(tx.inputs)[0]
        source_addr = input_coinref.Address
        for order in tx.outputs:
            dest_addr = order.Address
            value = order.Value.ToString()  # fixed8
            if order.AssetId == Blockchain.Default().SystemShare().Hash:
                asset_name = 'NEO'
            else:
                asset_name = 'GAS'

            if source_addr != dest_addr:
                print(f"Sending {value} {asset_name} from {source_addr} to {dest_addr}")
            else:
                print(f"Returning {value} {asset_name} as change to {dest_addr}")
        print(" ")
        print("Enter your password to send to the network")

        # password prompt
        passwd = prompt("[Password]> ", is_password=True)
        if not wallet.ValidatePassword(passwd):
            print("Incorrect password")
            return

        standard_contract = wallet.GetStandardAddress()

        if scripthash_from is not None:
            signer_contract = wallet.GetContract(scripthash_from)
        else:
            signer_contract = wallet.GetContract(standard_contract)

        if not signer_contract.IsMultiSigContract and owners is None:
            data = standard_contract.Data
            tx.Attributes = [TransactionAttribute(usage=TransactionAttributeUsage.Script,
                                                  data=data)]

        # insert any additional user specified tx attributes
        tx.Attributes = tx.Attributes + user_tx_attributes

        if owners:
            owners = list(owners)
            for owner in owners:
                tx.Attributes.append(
                    TransactionAttribute(usage=TransactionAttributeUsage.Script, data=owner))

        context = ContractParametersContext(tx, isMultiSig=signer_contract.IsMultiSigContract)
        wallet.Sign(context)

        if owners:
            owners = list(owners)
            gather_signatures(context, tx, owners)

        if context.Completed:

            tx.scripts = context.GetScripts()
            relayed = NodeLeader.Instance().Relay(tx)

            if relayed:
                wallet.SaveTransaction(tx)

                print("Relayed Tx: %s " % tx.Hash.ToString())
                return tx
            else:

                print("Could not relay tx %s " % tx.Hash.ToString())

        else:
            print("Transaction initiated, but the signature is incomplete. Use the `sign` command with the information below to complete signing.")
            print(json.dumps(context.ToJson(), separators=(',', ':')))
            return

    except Exception as e:
        print("Could not send: %s " % e)
        traceback.print_stack()
        traceback.print_exc()

    return


def parse_and_sign(wallet, jsn):
    try:
        context = ContractParametersContext.FromJson(jsn)
        if context is None:
            print("Failed to parse JSON")
            return

        wallet.Sign(context)

        if context.Completed:

            print("Signature complete, relaying...")

            tx = context.Verifiable
            tx.scripts = context.GetScripts()

            wallet.SaveTransaction(tx)

            print("will send tx: %s " % json.dumps(tx.ToJson(), indent=4))

            relayed = NodeLeader.Instance().Relay(tx)

            if relayed:
                print("Relayed Tx: %s " % tx.Hash.ToString())
            else:
                print("Could not relay tx %s " % tx.Hash.ToString())
            return
        else:
            print("Transaction initiated, but the signature is incomplete")
            print(json.dumps(context.ToJson(), separators=(',', ':')))
            return

    except Exception as e:
        print("Could not send: %s " % e)
        traceback.print_stack()
        traceback.print_exc()
