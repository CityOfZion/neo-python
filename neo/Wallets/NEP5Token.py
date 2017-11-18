import binascii
import traceback

from decimal import getcontext, Decimal
from logzero import logger

from neo.Core.VerificationCode import VerificationCode
from neo.Cryptography.Crypto import Crypto
from neo.Prompt.Commands.Invoke import TestInvokeContract
from neo.Prompt.Utils import parse_param
from neo.UInt160 import UInt160


class NEP5Token(VerificationCode):

    name = None
    symbol = None
    decimals = None

    _address = None

    def __init__(self, script=None):

        param_list = bytearray(b'\x07\x10')
        super(NEP5Token, self).__init__(script=script, param_list=param_list)

    def SetScriptHash(self, script_hash):
        self._scriptHash = script_hash

    @staticmethod
    def FromDBInstance(db_token):
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
        if self._address is None:
            self._address = Crypto.ToAddress(self.ScriptHash)
        return self._address

    def Query(self, wallet):

        if self.name is not None:
            # don't query twice
            return

        invoke_args = [self.ScriptHash.ToString(), parse_param('name'), []]
        invoke_args2 = [self.ScriptHash.ToString(), parse_param('symbol'), []]
        invoke_args3 = [self.ScriptHash.ToString(), parse_param('decimals'), []]
        tx, fee, nameResults, num_ops = TestInvokeContract(wallet, invoke_args, None, False)
        tx, fee, symbolResults, num_ops = TestInvokeContract(wallet, invoke_args2, None, False)
        tx, fee, decimalResults, num_ops = TestInvokeContract(wallet, invoke_args3, None, False)

        try:

            self.name = nameResults[0].GetString()
            self.symbol = symbolResults[0].GetString()
            self.decimals = decimalResults[0].GetBigInteger()
            return True
        except Exception as e:
            logger.error("could not query token %s " % e)

        return False

    def GetBalance(self, wallet, address, as_string=False):

        if type(address) is UInt160:
            address = Crypto.ToAddress(address)

        invoke_args = [self.ScriptHash.ToString(), parse_param('balanceOf'), [parse_param(address)]]
        tx, fee, balanceResults, num_ops = TestInvokeContract(wallet, invoke_args, None, False)

        try:
            val = balanceResults[0].GetBigInteger()
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

        invoke_args = [self.ScriptHash.ToString(), 'transfer',
                       [parse_param(from_addr), parse_param(to_addr), parse_param(amount)]]

        tx, fee, results, num_ops = TestInvokeContract(wallet, invoke_args, None, True)

        return tx, fee, results

    def TransferFrom(self, wallet, from_addr, to_addr, amount):
        invoke_args = [self.ScriptHash.ToString(), 'transferFrom',
                       [parse_param(from_addr), parse_param(to_addr), parse_param(amount)]]

        tx, fee, results, num_ops = TestInvokeContract(wallet, invoke_args, None, True)

        return tx, fee, results

    def Allowance(self, wallet, owner_addr, requestor_addr):
        invoke_args = [self.ScriptHash.ToString(), 'allowance',
                       [parse_param(owner_addr), parse_param(requestor_addr), parse_param(0)]]

        tx, fee, results, num_ops = TestInvokeContract(wallet, invoke_args, None, True)

        return tx, fee, results

    def Approve(self, wallet, owner_addr, requestor_addr, amount):
        invoke_args = [self.ScriptHash.ToString(), 'approve',
                       [parse_param(owner_addr), parse_param(requestor_addr), parse_param(amount)]]

        tx, fee, results, num_ops = TestInvokeContract(wallet, invoke_args, None, True)

        return tx, fee, results

    def ToJson(self):
        jsn = {
            'name': self.name,
            'symbol': self.symbol,
            'decimals': self.decimals,
            'script_hash': self.ScriptHash.ToString(),
            'contract address': self.Address
        }
        return jsn
