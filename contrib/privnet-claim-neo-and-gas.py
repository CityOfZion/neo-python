#!/usr/bin/env python3

"""
privnet-claim-neo-and-gas.py

With this script you can transfer all NEO from the default contract on a private network
such as the one created by the neo-privatenet-docker image, without having to
use the neo-gui client (or Windows at all). It also waits a little bit to generate
GAS and claims it.

The output of the script is two things:

* A wallet with 100,000,000 NEO and 48 GAS (after 1 minute) which you can use with prompt.py
* A WIF private key you can use with any client.

Run it like this:

    python3 contrib/privnet-claim-neo-and-gas.py

There are several parameters you can configure with cli args. Take a look at the help:

    python3 contrib/privnet-claim-neo-and-gas.py -h

This script takes several minutes to complete. Be patient!
"""

import os
import sys
import json
import time
import datetime
import argparse

# Allow importing 'neo' from parent path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, parent_dir)

from tempfile import NamedTemporaryFile
from Crypto import Random

from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Wallets.KeyPair import KeyPair
from neo.Prompt.Commands.LoadSmartContract import ImportMultiSigContractAddr
from neo.Core.Blockchain import Blockchain
from neo.Fixed8 import Fixed8
from neo.Prompt.Commands.Send import construct_and_send
from neo.Prompt.Commands.Wallet import ClaimGas
from neo.Core.TX.Transaction import TransactionOutput, ContractTransaction
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neo.Network.NodeLeader import NodeLeader
from twisted.internet import reactor, task
from neo.Settings import settings

WALLET_PATH = "/tmp/privnet1"
WALLET_PWD = "neo"
MINUTES_TO_WAIT_UNTIL_GAS_CLAIM = 1

# default multi-sig contract from the neo-privatenet-docker image. If you are using a different private net
# configuration, you'll need to add all your node keys and multi-sig address in place of the ones below

multisig_addr = 'AZ81H31DMWzbSnFDLFkzh9vHwaDLayV7fU'
nodekeys = {'02b3622bf4017bdfe317c58aed5f4c753f206b7db896046fa7d774bbc4bf7f8dc2': 'KxyjQ8eUa4FHt3Gvioyt1Wz29cTUrE4eTqX3yFSk1YFCsPL8uNsY',
            '02103a7f7dd016558597f7960d27c516a4394fd968b9e65155eb4b013e4040406e': 'KzfPUYDC9n2yf4fK5ro4C8KMcdeXtFuEnStycbZgX3GomiUsvX6W',
            '03d90c07df63e690ce77912e10ab51acc944b66860237b608c4f8f8309e71ee699': 'L2oEXKRAAMiPEZukwR5ho2S6SMeQLhcK9mF71ZnF7GvT8dU4Kkgz',
            '02a7bc55fe8684e0119768d104ba30795bdcc86619e864add26156723ed185cd62': 'KzgWE3u3EDp13XPXXuTKZxeJ3Gi8Bsm8f9ijY3ZsCKKRvZUo1Cdn'}


class PrivnetClaimall(object):
    start_height = None
    start_dt = None
    _walletdb_loop = None

    wallet_fn = None
    wallet_pwd = None
    min_wait = None
    wif_fn = None

    def __init__(self, wallet_fn, wallet_pwd, min_wait, wif_fn):
        self.wallet_fn = wallet_fn
        self.wallet_pwd = wallet_pwd
        self.min_wait = min_wait
        self.wif_fn = wif_fn

        self.start_height = Blockchain.Default().Height
        self.start_dt = datetime.datetime.utcnow()

    def quit(self):
        print('Shutting down.  This may take a bit...')
        self.go_on = False
        Blockchain.Default().Dispose()
        reactor.stop()
        NodeLeader.Instance().Shutdown()

    @staticmethod
    def send_neo(wallet, address_from, address_to, amount):
        assetId = None

        assetId = Blockchain.Default().SystemShare().Hash

        scripthash_to = wallet.ToScriptHash(address_to)
        scripthash_from = wallet.ToScriptHash(address_from)

        f8amount = Fixed8.TryParse(amount)

        if f8amount.value % pow(10, 8 - Blockchain.Default().GetAssetState(assetId.ToBytes()).Precision) != 0:
            raise Exception("incorrect amount precision")

        fee = Fixed8.Zero()

        output = TransactionOutput(AssetId=assetId, Value=f8amount, script_hash=scripthash_to)
        tx = ContractTransaction(outputs=[output])
        ttx = wallet.MakeTransaction(tx=tx, change_address=None, fee=fee, from_addr=scripthash_from)

        if ttx is None:
            raise Exception("insufficient funds, were funds already moved from multi-sig contract?")

        context = ContractParametersContext(tx, isMultiSig=True)
        wallet.Sign(context)

        if context.Completed:
            raise Exception("Something went wrong, multi-sig transaction failed")

        else:
            print("Transaction initiated")
            return json.dumps(context.ToJson(), separators=(',', ':'))

    def sign_and_finish(self, wallet, jsn):

        context = ContractParametersContext.FromJson(jsn)
        if context is None:
            print("Failed to parse JSON")
            return None

        wallet.Sign(context)

        if context.Completed:

            print("Signature complete, relaying...")

            tx = context.Verifiable
            tx.scripts = context.GetScripts()

            wallet.SaveTransaction(tx)

            print("will send tx: %s " % json.dumps(tx.ToJson(), indent=4))

            relayed = NodeLeader.Instance().Relay(tx)

            if relayed:
                print("Relayed Tx: %s " % tx.Hash.ToString())
                self.wait_for_tx(tx)
                return('success')

            else:
                print("Could not relay tx %s " % tx.Hash.ToString())
                return('fail')
        else:
            print("Transaction signed, but the signature is still incomplete")
            return(json.dumps(context.ToJson(), separators=(',', ':')))

    def wait_for_tx(self, tx, max_seconds=300):
        """ Wait for tx to show up on blockchain """
        foundtx = False
        sec_passed = 0
        while not foundtx and sec_passed < max_seconds:
            _tx, height = Blockchain.Default().GetTransaction(tx.Hash.ToString())
            if height > -1:
                foundtx = True
                continue
            print("Waiting for tx {} to show up on blockchain...".format(tx.Hash.ToString()))
            time.sleep(3)
            sec_passed += 3
        if foundtx:
            return True
        else:
            print("Transaction was relayed but never accepted by consensus node")
            return False

    def run(self):
        dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
        dbloop.start(.1)
        Blockchain.Default().PersistBlocks()

        while Blockchain.Default().Height < 2:
            print("Waiting for wallet to sync...")
            time.sleep(1)

        print("Creating Wallet...")
        self.wallet = UserWallet.Create(path=self.wallet_fn, password=self.wallet_pwd)
        self.wallet.ProcessBlocks()

        # Extract infos from wallet
        contract = self.wallet.GetDefaultContract()
        key = self.wallet.GetKey(contract.PublicKeyHash)
        address = key.GetAddress()
        wif = key.Export()
        print("- Address:", address)
        print("- WIF key:", wif)
        self.wallet = None

        # Claim initial NEO
        self.claim_initial_neo(address)

        # Open wallet again
        self.wallet = UserWallet.Open(self.wallet_fn, self.wallet_pwd)
        self._walletdb_loop = task.LoopingCall(self.wallet.ProcessBlocks)
        self._walletdb_loop.start(1)

        print("\nWait %s min before claiming GAS." % self.min_wait)
        time.sleep(60 * self.min_wait)

        print("\nSending NEO to own wallet...")
        tx = construct_and_send(None, self.wallet, ["neo", address, "100000000"], prompt_password=False)
        if not tx:
            print("Something went wrong, no tx.")
            return

        # Wait until transaction is on blockchain
        self.wait_for_tx(tx)

        print("Claiming the GAS...")
        claim_tx, relayed = ClaimGas(self.wallet, require_password=False)
        self.wait_for_tx(claim_tx)

        # Finally, need to rebuild the wallet
        self.wallet.Rebuild()

        print("\nAll done!")
        print("- WIF key: %s" % wif)
        print("- Wallet file: %s" % self.wallet_fn)
        print("- Wallet pwd: %s" % self.wallet_pwd)

        if self.wif_fn:
            with open(self.wif_fn, "w") as f:
                f.write(wif)

        self.quit()

    def claim_initial_neo(self, target_address):
        wallets = []
        i = 0
        tx_json = None
        dbloops = []

        print("Signing new transaction with 3 of 4 node keys...")
        for pkey, wif in nodekeys.items():
            walletpath = "wallet{}.db3".format(i + 1)
            if os.path.exists(walletpath):
                os.remove(walletpath)
            wallet = UserWallet.Create(path=walletpath, password=self.wallet_pwd)
            wallets.append(wallet)

            print("Importing node private key to to {}".format(walletpath))
            prikey = KeyPair.PrivateKeyFromWIF(wif)
            wallet.CreateKey(prikey)

            print("Importing multi-sig contract to {}".format(walletpath))
            multisig_args = [pkey, '3']
            multisig_args.extend(list(nodekeys.keys()))
            ImportMultiSigContractAddr(wallet, multisig_args)

            dbloop = task.LoopingCall(wallet.ProcessBlocks)
            dbloop.start(1)
            dbloops.append(dbloop)

            # print("Wallet %s " % json.dumps(wallet.ToJson(), indent=4))

            if i == 0:
                print("Creating spend transaction to {}".format(target_address))
                tx_json = self.send_neo(wallet, multisig_addr, target_address, '100000000')
                if tx_json is None:
                    break
            else:
                tx_json = self.sign_and_finish(wallet, tx_json)

            if tx_json == 'success':
                print("Finished, {} should now own all the NEO on the private network.".format(target_address))
                break
            i += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", action="store", help="Filename of wallet that will be created (default: %s)" % WALLET_PATH, default=WALLET_PATH)
    parser.add_argument("-p", "--password", action="store", help="Wallet password (default: %s)" % WALLET_PWD, default=WALLET_PWD)
    parser.add_argument("-t", "--time", action="store", help="Minutes to wait for the NEO to generate GAS (default: %s)" % MINUTES_TO_WAIT_UNTIL_GAS_CLAIM, default=MINUTES_TO_WAIT_UNTIL_GAS_CLAIM)
    parser.add_argument("-w", "--save-privnet-wif", action="store", help="Filename to store created privnet wif key")
    args = parser.parse_args()

    if os.path.isfile(args.output):
        print("Error: Wallet file %s already exists" % args.output)
        exit(1)

    settings.setup_privnet()
    print("Blockchain DB path:", settings.LEVELDB_PATH)
    if os.path.exists(settings.LEVELDB_PATH):
        print("Warning: Chain database already exists. If this is from a previous private network, you need to delete %s" % settings.LEVELDB_PATH)

    blockchain = LevelDBBlockchain(settings.LEVELDB_PATH)
    Blockchain.RegisterBlockchain(blockchain)

    reactor.suggestThreadPoolSize(15)
    NodeLeader.Instance().Start()

    pc = PrivnetClaimall(args.output, args.password, args.time, args.save_privnet_wif)
    reactor.callInThread(pc.run)
    reactor.run()
