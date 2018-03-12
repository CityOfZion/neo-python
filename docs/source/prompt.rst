
======
Prompt
======

This is the default interface for running and interacting with the NEO blockchain.

Usage::

    $ python prompt.py
    NEO cli. Type 'help' to get started

    neo>


----------------
Managing wallets
----------------

Create a wallet
^^^^^^^^^^^^^^^

.. code-block:: sh

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

Open a wallet
^^^^^^^^^^^^^

.. code-block:: sh

    neo> open wallet path/to/walletfile
    [Password]> ***********
    Opened wallet at path/to/walletfile
    neo>


Inspect a wallet
^^^^^^^^^^^^^^^^

.. code-block:: sh

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

Rebuild Wallet Index
^^^^^^^^^^^^^^^^^^^^
If your wallet is behaving unexepectedly or you have imported a new address into your wallet, it is a good idea to rebuild your wallet index.  This will sync the wallet from the beginning of the chain.  Optionally, you can specify a block number to start the resync at

.. code-block:: sh

    neo> wallet rebuild 700000
    restarting at 700000
    neo>

Migrate your wallet
^^^^^^^^^^^^^^^^^^^
If there have been changes to the wallet data model, you may need to migrate your wallet

.. code-block:: sh

    neo> wallet migrated
    migrated wallet
    neo>


Reencrypt your wallet
^^^^^^^^^^^^^^^^^^^^^
If you get a message like this when opening your wallet, you must reencrypt in order to secure against previous wallet vulnerabilities.

.. code-block:: sh

  Could not open wallet: This wallet is currently vulnerable. Please execute the "reencrypt_wallet.py" script on this wallet before continuing

You can fix this by ``exit`` the neo prompt, and run the re-encryption script:

.. code-block:: sh

  python reencrypt_wallet.py path/to/mywallet.db3

This will ask you for a password and re-save the reencrypted wallet with a new name of ``path/to/new_mywallet.db3``.

Import WIF
^^^^^^^^^^
You may want to import a `WIF <https://en.bitcoin.it/wiki/Wallet_import_format>`_ key to add an address to your wallet

.. code-block:: sh

    neo> import wif KxP97gujib35PBEnTq78e5NmYVbeaosU4AdguDzZ4tyf6a7W32UM
    Imported key KxP97gujib35PBEnTq78e5NmYVbeaosU4AdguDzZ4tyf6a7W32UM
    Pubkey: 303263383231666338336465373331313039633435653034346136353863386631313337623730303461396232323237613335653262353566613061313630323731
    neo>

Export WIF
^^^^^^^^^^
You may want to export a `WIF <https://en.bitcoin.it/wiki/Wallet_import_format>`_ key from your wallet to use in another program. Specify the address of the ``WIF`` you would like to export.

.. code-block:: sh

    neo> export wif AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK
    [Wallet Password]> ***********
    WIF key export: KxP97gujib35PBEnTq78e5NmYVbeaosU4AdguDzZ4tyf6a7W32UM
    neo>

Import NEP2 Passphrase protected WIF
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can import a `NEP2 <https://github.com/neo-project/proposals/blob/master/nep-2.mediawiki>`_ encrypted private key like this:

.. code-block:: sh

    neo> import nep2 6PYVPVe1fQznphjbUxXP9KZJqPMVnVwCx5s5pr5axRJ8uHkMtZg97eT5kL
    [Key Password]> ******************
    Imported nep2 key: 6PYVPVe1fQznphjbUxXP9KZJqPMVnVwCx5s5pr5axRJ8uHkMtZg97eT5kL
    Pubkey: 303236323431653765323662333862623731353462386164343934353862393766623163343739373434336463393231633563613537373466353131613262626663

Export NEP2 Passphrase protected WIF
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can export an address as `NEP2 <https://github.com/neo-project/proposals/blob/master/nep-2.mediawiki>`_ encrypted private key like this:

.. code-block:: sh

    neo> export nep2 AStZHy8E6StCqYQbzMqi4poH7YNDHQKxvt
    [Wallet Password]> ***********
    [Key Password 1]> ******************
    [Key Password 2]> ******************
    NEP2 key export: 6PYVPVe1fQznphjbUxXP9KZJqPMVnVwCx5s5pr5axRJ8uHkMtZg97eT5kL
    neo>


Delete address
^^^^^^^^^^^^^^

.. code-block:: sh

    neo> wallet delete_addr AStZHy8E6StCqYQbzMqi4poH7YNDHQKxvt
    Deleted address AStZHy8E6StCqYQbzMqi4poH7YNDHQKxvt
    neo>

Import *watch only* address
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A **watch only** address is any address that you do not have the public key for that you may want to observe. A **watch only** address can be deleted just like a normal address.

.. code-block:: sh

    neo> import watch_addr AStZHy8E6StCqYQbzMqi4poH7YNDHQKxvt
    neo>



Import a Smart Contract address
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You may have a smart contract which has been deployed that you want to use funds from.  Depending on how it is programmed, it may allow you to use funds from it as if it were your own.  In that case, you can import a contract address by specifying the ``script_hash`` of the contract and the ``public key`` of the address in your wallet you want the contract associated with.  A contract address can be deleted from your wallet in the same way as a normal address.

.. code-block:: sh

    # import contract_addr {script_hash} {pubkey}
    neo> import contract_addr 3c62006802d895974069a1d96398a04b4703f0f8 027973267230b7cba0724589653e667ddea7aa8479c01a82bf8dd398cec93508ef
    Added contract addres AeU8kTJxynwkT3q9ao8aDFuaRJBkU3AfFG to wallet
    neo>


--------------
Sending Assets
--------------

Basic Send
^^^^^^^^^^

You may send assets from your wallet using the following command.  Note that with this syntax, assets will be chosen from your addresses for you, and may come from multiple addresses.  Also note that the ``change_address`` of the transaction will be one of the addresses in your wallet.

.. code-block:: sh

    # syntax send {asset_name} {address to} {amount} ( optional: --from-addr={from_addr})
    neo> send gas AeU8kTJxynwkT3q9ao8aDFuaRJBkU3AfFG 11
    [Password]> ***********
    Relayed Tx: 468e294b11a9f65cc5e2c372124877472eebf121befb77ceed23a84862a606d3
    neo>


Send From
^^^^^^^^^

You may also specify a particular address to send assets from. This is especially useful when sending from contract addresses.

.. code-block:: sh

    # syntax send {asset_name} {address to} {amount} ( optional: --from-addr={from_addr})
    neo> send gas AeU8kTJxynwkT3q9ao8aDFuaRJBkU3AfFG 11 --from-addr=AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK
    [Password]> ***********
    Relayed Tx: a43dfb30af63bd0e5a510b05f02b3d40932af26d4564e040e3812ce78e76ce71
    neo>




-----------
NEP5 Tokens
-----------

Import NEP5 Compliant Token
^^^^^^^^^^^^^^^^^^^^^^^^^^^

You may want to observe or interact with ``NEP5`` Tokens with your wallet.  To do so, you must first register your wallet to observe a token.

.. code-block:: sh

    neo> import token f8d448b227991cf07cb96a6f9c0322437f1599b9
    added token {
        "name": "NEP5 Standard",
        "script_hash": "f8d448b227991cf07cb96a6f9c0322437f1599b9",
        "decimals": 8,
        "symbol": "NEP5",
        "contract address": "AYhE3Svuqdfh1RtzvE8hUhNR7HSpaSDFQg"
    }
    neo> wallet
    Wallet {
        # truncated ...

        "percent_synced": 100,
        "addresses": [
            "AayaivCAcYnM8q79JCrfpRGXrCEHJRN5bV",
            {
                "balances": {
                    "c56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b": "4051.0",
                    "602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7": "897.48372409"
                },
                "script_hash": "AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK",
                "votes": [],
                "version": 0,
                "is_watch_only": false,
                "tokens": [
                    "[f8d448b227991cf07cb96a6f9c0322437f1599b9] NEP5 : 4519175.65580000"
                ],
                "frozen": false
            },
            {
        }
    }




-----------------------------
Smart Contracts in the prompt
-----------------------------

View a full description of interacting with smart contracts in the prompt:  :ref:`Smart Contracts within the Prompt`

----------------------------
Retrieving NEO TestNet funds
----------------------------

This section explains how to obtain the TesNet funds requested via the official NEO `request form <https://neo.org/testnet>`_.

Obtaining the funds requires 2 steps

1. Adding a multi signature address to your wallet.
2. Transfering the funds to your own address.

Adding a multi signature address
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
For this we'll need 2 pieces of information

1. The public key sent in the email you received from NEO.
2. A public key from our own wallet. Have your wallet open and type ``wallet`` in the prompt to obtain the needed information.

.. code-block:: sh

    neo> wallet
    Wallet {
        ...
        "public_keys": [
            {
                "Address": "ANFLgwKG8Eni9gJmKfM7yFXEaWwoGkSUid",
                "Public Key": "037b8992e8384212f82e05c8836816c0f14dff9528397138731638b17d6357021e" <--- take this
            }
        ],
        ...
    }


Next we create the multi signature address as follows.

.. code-block:: sh

    neo> import multisig_addr
    please specify multisig contract like such: 'import multisig {pubkey in wallet} {minimum # of signatures required} {signing pubkey 1} {signing pubkey 2}...'

    neo> import multisig_addr 037b8992e8384212f82e05c8836816c0f14dff9528397138731638b17d6357021e 1 037b8992e8384212f82e05c8836816c0f14dff9528397138731638b17d6357021e 02883118351f8f47107c83ab634dc7e4
    ffe29d274e7d3dcf70159c8935ff769beb
    [I 180310 16:49:19 UserWallet:191] contract does not exist yet
    Added multi-sig contract address ALXEKioZntX73QawcnfcHUDvTVm8qXjAxf to wallet


Inspect your wallet again and you should see your balance (specifically look at the ``synced_balances`` key). If you don't see the added balance then run ``wallet rebuild`` and wait until it's fully synced and try again.

.. code-block:: sh

    neo> wallet
    Wallet {
        "path": "test",
        "addresses": [
            {
                "address": "ANFLgwKG8Eni9gJmKfM7yFXEaWwoGkSUid",
                "script_hash": "47028f2a3d33466f29fba10e65c90fd8f3d01e1f",
                "tokens": null
            },
            {
                "version": 0,
                "script_hash": "ALXEKioZntX73QawcnfcHUDvTVm8qXjAxf",
                "frozen": false,
                "votes": [],
                "balances": {
                    "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b": "50.0",
                    "0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7": "50.0"
                },
                "is_watch_only": false
            }
        ],
        ...
        "synced_balances": [
            "[NEO]: 50.0 ",
            "[NEOGas]: 50.0 "
        ],
        "public_keys": [
            {
                "Address": "ANFLgwKG8Eni9gJmKfM7yFXEaWwoGkSUid",
                "Public Key": "037b8992e8384212f82e05c8836816c0f14dff9528397138731638b17d6357021e"
            },
            {
                "Address": "ALXEKioZntX73QawcnfcHUDvTVm8qXjAxf",
                "Public Key": "037b8992e8384212f82e05c8836816c0f14dff9528397138731638b17d6357021e"
            }
        ],
        ...
    }


Transfering the funds to your own address.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now that we can access the funds we can send them to our own address as follows

.. code-block:: sh

    neo> send NEO ANFLgwKG8Eni9gJmKfM7yFXEaWwoGkSUid 5 --from-addr=ALXEKioZntX73QawcnfcHUDvTVm8qXjAxf
    [Password]> **********
    [I 180310 17:02:42 Transaction:611] Verifying transaction: b'c32b0e3d9adbef6720abfad5106dcd2dacb17b31d4f9d32cbcf8ed6e7f566ef3'
    Relayed Tx: c32b0e3d9adbef6720abfad5106dcd2dacb17b31d4f9d32cbcf8ed6e7f566ef3


Note that the ``--from-addr`` parameter specifies our multi signature contract address to take the funds from.