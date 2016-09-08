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
        if privateKey == None or len(privateKey) != 32:
            self.privateKey = random_to_priv(random_key())
        else:
            self.privateKey = privateKey

        self.publicKey = privkey_to_pubkey(self.privateKey)
        redeemScript = pubkey_to_redeem(self.publicKey)
        self.scriptHash = redeem_to_scripthash(redeemScript)
        self.address = scripthash_to_address(self.scriptHash)
