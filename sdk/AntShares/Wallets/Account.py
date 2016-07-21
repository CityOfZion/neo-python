# -*- coding:utf-8 -*-
"""
Description:
    Account class in AntShares.Wallets
Usage:
    from AntShares.Wallets.Account import Account
"""


import binascii


from AntShares.Cryptography.account import *


class Account(object):
    """docstring for Account"""
    def __init__(self, privkey=None):
        super(Account, self).__init__()
        self.privkey = privkey
        self.pubkey = None

    def create(self):
        if self.privkey == None:
            self.privkey = random_to_priv(random_key())

        self.pubkey = privkey_to_pubkey(self.privkey)
        redeemscript = pubkey_to_redeem(self.pubkey)
        scripthash = redeem_to_scripthash(redeemscript)
        self.address = scripthash_to_address(scripthash)
