# -*- coding:utf-8 -*-
"""
Description:
    Account class in AntShares.Wallets
Usage:
    from AntShares.Wallets.Account import Account
"""


import binascii


from AntShares.Cryptography.Helper import *


class Account(object):
    """docstring for Account"""
    def __init__(self, privateKey=None):
        super(Account, self).__init__()
        if privateKey == None:
            self.privateKey = random_to_priv(random_key())

        self.publicKey = None
        self.publicKeyHash = None

        self.pubkey = privkey_to_pubkey(self.privkey)
        redeemscript = pubkey_to_redeem(self.pubkey)
        scripthash = redeem_to_scripthash(redeemscript)
        self.address = scripthash_to_address(scripthash)
