
==========
neo-python
==========

This is the default interface for running and interacting with the NEO blockchain

Usage::

    $ python prompt.py
    NEO cli. Type 'help' to get started

    neo>


----------------
managing wallets
----------------

* create a wallet

    neo> create wallet path/to/walletfile
    [Password 1]> **********
    [Password 2]> **********
    Wallet {
        "addresses": [
            "AayaivCAcYnM8q79JCrfpRGXrCEHJRN5bV"
        ],
        "claims": {
            "available": 0.0,
            "unavailable": 0.0
        },
        "tokens": [],
        "height": 0,
        "synced_balances": [],
        "path": "Wallets/blahblah.db3",
        "public_keys": [
            {
                "Address": "AayaivCAcYnM8q79JCrfpRGXrCEHJRN5bV",
                "Public Key": "027973267230b7cba0724589653e667ddea7aa8479c01a82bf8dd398cec93508ef"
            }
        ],
        "percent_synced": 0
    }
    neo>


* open a wallet

    neo> open wallet path/to/walletfile
    [Password]> ***********
    Opened wallet at path/to/walletfile
    neo>

* inspect a wallet

    neo> wallet
    Wallet {
        "addresses": [
            "AayaivCAcYnM8q79JCrfpRGXrCEHJRN5bV"
        ],
        "claims": {
            "available": 0.0,
            "unavailable": 0.0
        },
        "tokens": [],
        "height": 75500,
        "synced_balances": [],
        "path": "Wallets/blahblah.db3",
        "public_keys": [
            {
                "Address": "AayaivCAcYnM8q79JCrfpRGXrCEHJRN5bV",
                "Public Key": "027973267230b7cba0724589653e667ddea7aa8479c01a82bf8dd398cec93508ef"
            }
        ],
        "percent_synced": 9
    }

