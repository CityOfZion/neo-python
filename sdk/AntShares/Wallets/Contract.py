# -*- coding:utf-8 -*-
"""
Description:
    Contract class in AntShares.Wallets
    Base class of all contracts
Usage:
    from AntShares.Wallets.Contract import Contract
"""

from AntShares.Cryptography.account import from_int_to_byte, bin_hash160, bin_to_b58check


class Contract(object):
    """docstring for Contract"""
    def __init__(self):
        super(Contract, self).__init__()
        self.redeemscript = None  # Contract script
        self.publickeyhash = None  # Hash value of publick key
        self._address = None  # Contract address
        self.contract_parameter_type = None  # Parameters list of Contract Type
        self.scripthash = None

    def get_address(self):
        if self._address == None:
            self._address = self.scripthash_to_address(self.scripthash)
        return self._address

    def equals(self, other):
        if id(self) == id(other):
            return True
        if not isinstance(other, Contract):
            return False
        return self.scripthash == other.scripthash

    def get_hashcode(self):
        if self.scripthash == None:
            self.scripthash = self.redeem_to_scripthash(self.redeem)
        return scripthash

    def pubkey_to_redeem(self, pubkey):
        return binascii.unhexlify('21'+ pubkey) + from_int_to_byte(int('ac',16))

    def redeem_to_scripthash(self, redeem):
        return binascii.hexlify(bin_hash160(redeem))

    def scripthash_to_address(self, scripthash):
        return bin_to_b58check(binascii.unhexlify(scripthash),int('17',16))
