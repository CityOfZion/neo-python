import binascii
import traceback

from decimal import Decimal
from logzero import logger

from neo.Core.VerificationCode import VerificationCode
from neocore.Cryptography.Crypto import Crypto
from neo.Prompt.Commands.Invoke import TestInvokeContract, test_invoke
from neo.Prompt.Utils import parse_param
from neocore.UInt160 import UInt160
from neo.VM.ScriptBuilder import ScriptBuilder


class NEP5Token(VerificationCode):
    name = None
    symbol = None
    decimals = None

    _address = None

    def __init__(self, script=None):
        """
        Create an instance.

        Args:
            script (bytes): (Optional)
        """
        param_list = bytearray(b'\x07\x10')
        super(NEP5Token, self).__init__(script=script, param_list=param_list)

    def SetScriptHash(self, script_hash):
        """
        Set the script hash to the specified value.
        Args:
            script_hash (UInt160):
        """
        self._scriptHash = script_hash

    @staticmethod
    def FromDBInstance(db_token):
        """
        Get a NEP5Token instance from a database token.

        Args:
            db_token (neo.Implementations.Wallets.peewee.Models.NEP5Token):

        Returns:
            NEP5Token: self.
        """
        hash_ar = bytearray(binascii.unhexlify(db_token.ContractHash))
        hash_ar.reverse()
        hash = UInt160(data=hash_ar)
        token = NEP5Token(script=None)
        token.SetScriptHash(hash)
        token.name = db_token.Name
        token.symbol = db_token.Symbol
        token.decimals = db_token.Decimals
        return token

    @property
    def Address(self):
        """
        Get the wallet address associated with the token.

        Returns:
            str: base58 encoded string representing the wallet address.
        """
        if self._address is None:
            self._address = Crypto.ToAddress(self.ScriptHash)
        return self._address

    def Query(self, wallet):
        """
        Query the smart contract for its token information (name, symbol, decimals).

        Args:
            wallet (neo.Wallets.Wallet): a wallet instance.

        Returns:
            None: if the NEP5Token instance `Name` is already set.
            True: if all information was retrieved.
            False: if information retrieval failed.
        """
        if self.name is not None:
            # don't query twice
            return

        sb = ScriptBuilder()
        sb.EmitAppCallWithOperation(self.ScriptHash, 'name')
        sb.EmitAppCallWithOperation(self.ScriptHash, 'symbol')
        sb.EmitAppCallWithOperation(self.ScriptHash, 'decimals')

        tx, fee, results, num_ops = test_invoke(sb.ToArray(), wallet, [])

        try:
            self.name = results[0].GetString()
            self.symbol = results[1].GetString()
            self.decimals = results[2].GetBigInteger()
            return True
        except Exception as e:
            logger.error("could not query token %s " % e)
        return False

    def GetBalance(self, wallet, address, as_string=False):
        """
        Get the token balance.

        Args:
            wallet (neo.Wallets.Wallet): a wallet instance.
            address (str): public address of the account to get the token balance of.
            as_string (bool): whether the return value should be a string. Default is False, returning an integer.

        Returns:
            int/str: token balance value as int (default), token balanace as string if `as_string` is set to True. 0 if balance retrieval failed.
        """
        addr = parse_param(address, wallet)
        if isinstance(addr, UInt160):
            addr = addr.Data
        sb = ScriptBuilder()
        sb.EmitAppCallWithOperationAndArgs(self.ScriptHash, 'balanceOf', [addr])

        tx, fee, results, num_ops = test_invoke(sb.ToArray(), wallet, [])

        try:
            val = results[0].GetBigInteger()
            precision_divisor = pow(10, self.decimals)
            balance = Decimal(val) / Decimal(precision_divisor)
            if as_string:
                formatter_str = '.%sf' % self.decimals
                balance_str = format(balance, formatter_str)
                return balance_str
            return balance
        except Exception as e:
            logger.error("could not get balance: %s " % e)
            traceback.print_stack()

        return 0

    def Transfer(self, wallet, from_addr, to_addr, amount):
        """
        Transfer a specified amount of the NEP5Token to another address.

        Args:
            wallet (neo.Wallets.Wallet): a wallet instance.
            from_addr (str): public address of the account to transfer the given amount from.
            to_addr (str): public address of the account to transfer the given amount to.
            amount (int): quantity to send.

        Returns:
            tuple:
                InvocationTransaction: the transaction.
                int: the transaction fee.
                list: the neo VM evaluationstack results.
        """
        sb = ScriptBuilder()
        sb.EmitAppCallWithOperationAndArgs(self.ScriptHash, 'transfer',
                                           [parse_param(from_addr, wallet), parse_param(to_addr, wallet),
                                            parse_param(amount)])

        tx, fee, results, num_ops = test_invoke(sb.ToArray(), wallet, [], from_addr=from_addr)

        return tx, fee, results

    def TransferFrom(self, wallet, from_addr, to_addr, amount):
        """
        Transfer a specified amount of a token from the wallet specified in the `from_addr` to the `to_addr`
        if the originator `wallet` has been approved to do so.

        Args:
            wallet (neo.Wallets.Wallet): a wallet instance.
            from_addr (str): public address of the account to transfer the given amount from.
            to_addr (str): public address of the account to transfer the given amount to.
            amount (int): quantity to send.

        Returns:
            tuple:
                InvocationTransaction: the transaction.
                int: the transaction fee.
                list: the neo VM evaluation stack results.
        """
        invoke_args = [self.ScriptHash.ToString(), 'transferFrom',
                       [parse_param(from_addr, wallet), parse_param(to_addr, wallet), parse_param(amount)]]

        tx, fee, results, num_ops = TestInvokeContract(wallet, invoke_args, None, True)

        return tx, fee, results

    def Allowance(self, wallet, owner_addr, requestor_addr):
        """
        Return the amount of tokens that the `requestor_addr` account can transfer from the `owner_addr` account.

        Args:
            wallet (neo.Wallets.Wallet): a wallet instance.
            owner_addr (str): public address of the account to transfer the given amount from.
            requestor_addr (str): public address of the account that requests the transfer.

        Returns:
            tuple:
                InvocationTransaction: the transaction.
                int: the transaction fee.
                list: the neo VM evaluation stack results.
        """
        invoke_args = [self.ScriptHash.ToString(), 'allowance',
                       [parse_param(owner_addr, wallet), parse_param(requestor_addr, wallet)]]

        tx, fee, results, num_ops = TestInvokeContract(wallet, invoke_args, None, True)

        return tx, fee, results

    def Approve(self, wallet, owner_addr, requestor_addr, amount):
        """
        Approve the `requestor_addr` account to transfer `amount` of tokens from the `owner_addr` acount.

        Args:
            wallet (neo.Wallets.Wallet): a wallet instance.
            owner_addr (str): public address of the account to transfer the given amount from.
            requestor_addr (str): public address of the account that requests the transfer.
            amount (int): quantity to send.

        Returns:
            tuple:
                InvocationTransaction: the transaction.
                int: the transaction fee.
                list: the neo VM evaluation stack results.
        """
        invoke_args = [self.ScriptHash.ToString(), 'approve',
                       [parse_param(owner_addr, wallet), parse_param(requestor_addr, wallet), parse_param(amount)]]

        tx, fee, results, num_ops = TestInvokeContract(wallet, invoke_args, None, True)

        return tx, fee, results

    def Mint(self, wallet, mint_to_addr, attachment_args):
        """
        Call the "mintTokens" function of the smart contract.

        Args:
            wallet (neo.Wallets.Wallet): a wallet instance.
            mint_to_addr (str): public address of the account to mint the tokens to.
            attachment_args: (list): a list of arguments used to attach neo and/or gas to an invoke, eg ['--attach-gas=10.0','--attach-neo=3']

        Returns:
            tuple:
                InvocationTransaction: the transaction.
                int: the transaction fee.
                list: the neo VM evaluation stack results.
        """
        invoke_args = [self.ScriptHash.ToString(), 'mintTokens', []]

        invoke_args = invoke_args + attachment_args

        tx, fee, results, num_ops = TestInvokeContract(wallet, invoke_args, None, True, from_addr=mint_to_addr)

        return tx, fee, results

    def CrowdsaleRegister(self, wallet, register_addresses):
        """
        Register for a crowd sale.

        Args:
            wallet (neo.Wallets.Wallet): a wallet instance.
            register_addresses (str): public address of the account that wants to register for the sale.

        Returns:
            tuple:
                InvocationTransaction: the transaction.
                int: the transaction fee.
                list: the neo VM evaluation stack results.
        """
        invoke_args = [self.ScriptHash.ToString(), 'crowdsale_register',
                       [parse_param(p, wallet) for p in register_addresses]]

        tx, fee, results, num_ops = TestInvokeContract(wallet, invoke_args, None, True)

        return tx, fee, results

    def ToJson(self):
        """
        Convert object members to a dictionary that can be parsed as JSON.

        Returns:
             dict:
        """
        jsn = {
            'name': self.name,
            'symbol': self.symbol,
            'decimals': self.decimals,
            'script_hash': self.ScriptHash.ToString(),
            'contract address': self.Address
        }
        return jsn
