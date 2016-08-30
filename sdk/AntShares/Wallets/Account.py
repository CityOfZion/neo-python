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
        
        pubkey = privkey_to_pubkey('L1RrT1f4kXJGnF2hESU1AbaQQG82WqLsmWQWEPGm2fbrNLwdrAV9')
        pubkey = '21'+ pubkey
        pubkey = binascii.unhexlify(pubkey)
        RedeemScript = pubkey + from_int_to_byte(int('ac',16))
        print binascii.hexlify(RedeemScript)
        script_hash_ = binascii.hexlify(bin_hash160(RedeemScript))
        print script_hash_
        print bin_to_b58check(binascii.unhexlify(script_hash_),int('17',16))

    def export(self):
        pass
