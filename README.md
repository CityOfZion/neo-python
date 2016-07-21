antshares-python: Python for Antshares
=========================
 support Python 2.7
# Demo 

    random = random_key()
    privkey = random_to_priv(random)
    pubkey = privkey_to_pubkey(privkey)
    redeemscript = pubkey_to_redeem(pubkey)
    scripthash = redeem_to_scripthash(redeemscript)
    address = scripthash_to_address(scripthash)
