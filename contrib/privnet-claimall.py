#!/usr/bin/env python3

"""
privnet-claimall.py

This script will allow you do the initial claim to transfer all NEO from the default contract on
a private network such as the one created by the neo-privatenet-docker image, without having to
use the neo-gui client (or Windows at all).

Set up the neo-python config file (config.testnet.json) to point to your newly-created private
network nodes, create a wallet for transferring the NEO to, and then call this script as shown:

python3 privnet-claimall.py {address to receive all 100000000 NEO}

"""

import os
import sys
import json
import time
import datetime

if os.getcwd().endswith("/contrib"):
    os.chdir('../')  # use config and Chains folder from main directory

sys.path.append(os.getcwd())

from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Wallets.KeyPair import KeyPair
from neo.Prompt.Commands.LoadSmartContract import ImportMultiSigContractAddr
from neo.Prompt.Notify import SubscribeNotifications
from neo.Core.Blockchain import Blockchain
from neo.Fixed8 import Fixed8
from neo.Core.TX.Transaction import TransactionOutput,ContractTransaction
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neo.Network.NodeLeader import NodeLeader
from twisted.internet import reactor, task
from neo.Settings import settings

blockchain = LevelDBBlockchain(settings.LEVELDB_PATH)
Blockchain.RegisterBlockchain(blockchain)
SubscribeNotifications()

mypassword = 'supersekritpassword'

# default multi-sig contract from the neo-privatenet-docker image. If you are using a different private net
# configuration, you'll need to add all your node keys and multi-sig address in place of the ones below

multisig_addr = 'AZ81H31DMWzbSnFDLFkzh9vHwaDLayV7fU'
nodekeys = { '02b3622bf4017bdfe317c58aed5f4c753f206b7db896046fa7d774bbc4bf7f8dc2': 'KxyjQ8eUa4FHt3Gvioyt1Wz29cTUrE4eTqX3yFSk1YFCsPL8uNsY',
            '02103a7f7dd016558597f7960d27c516a4394fd968b9e65155eb4b013e4040406e': 'KzfPUYDC9n2yf4fK5ro4C8KMcdeXtFuEnStycbZgX3GomiUsvX6W',
            '03d90c07df63e690ce77912e10ab51acc944b66860237b608c4f8f8309e71ee699': 'L2oEXKRAAMiPEZukwR5ho2S6SMeQLhcK9mF71ZnF7GvT8dU4Kkgz',
            '02a7bc55fe8684e0119768d104ba30795bdcc86619e864add26156723ed185cd62': 'KzgWE3u3EDp13XPXXuTKZxeJ3Gi8Bsm8f9ijY3ZsCKKRvZUo1Cdn'}


class PrivnetClaimall(object):

    start_height = Blockchain.Default().Height
    start_dt = datetime.datetime.utcnow()

    def quit(self):
        print('Shutting down.  This may take a bit...')
        self.go_on = False
        Blockchain.Default().Dispose()
        reactor.stop()
        NodeLeader.Instance().Shutdown()

    @staticmethod
    def begin_send(wallet, arguments):

        to_send = arguments[0]
        address_to = arguments[1]
        amount = arguments[2]
        from_address = arguments[3]

        assetId = None

        if to_send == 'neo':
            assetId = Blockchain.Default().SystemShare().Hash
        else:
            assetId = Blockchain.Default().SystemCoin().Hash


        scripthash_to = wallet.ToScriptHash(address_to)
        scripthash_from = wallet.ToScriptHash(from_address)

        f8amount = Fixed8.TryParse(amount)

        if f8amount.value % pow(10, 8 - Blockchain.Default().GetAssetState(assetId.ToBytes()).Precision) != 0:
            print("incorrect amount precision")
            return

        fee = Fixed8.Zero()

        output = TransactionOutput(AssetId=assetId, Value=f8amount, script_hash=scripthash_to)
        tx = ContractTransaction(outputs=[output])
        ttx = wallet.MakeTransaction(tx=tx, change_address=None, fee=fee, from_addr=scripthash_from)

        if ttx is None:
            print("insufficient funds, were funds already moved from multi-sig contract?")
            return None

        context = ContractParametersContext(tx, isMultiSig=True)
        wallet.Sign(context)

        if context.Completed:
            print("Something went wrong, multi-sig transaction failed")
            return None

        else:
            print("Transaction initiated")
            return json.dumps(context.ToJson(), separators=(',', ':'))

    @staticmethod
    def sign_and_finish(wallet, jsn):

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
                foundtx = False
                count = 0
                while foundtx == False and count < 100:
                    try:
                        tx, height = Blockchain.Default().GetTransaction(tx.Hash.ToString())
                        if height > -1:
                            foundtx = True
                    except Exception as e:
                        print("Waiting for tx {} to show up on blockchain...".format(tx.Hash.ToString()))
                    time.sleep(3)
                    count += 1
                if foundtx == True:
                    return('success')
                else:
                    print("Transaction was relayed but never accepted by consensus node")
                    return('fail')
            else:
                print("Could not relay tx %s " % tx.Hash.ToString())
                return('fail')
        else:
            print("Transaction signed, but the signature is still incomplete")
            return(json.dumps(context.ToJson(), separators=(',', ':')))


    def run(self):

        to_addr = sys.argv[1]

        dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
        dbloop.start(.1)

        Blockchain.Default().PersistBlocks()

        wallets = []
        i = 0
        tx_json = ''

        print("Signing new transaction with 3 of 4 node keys...")

        for pkey, wif in nodekeys.items():
            walletpath="wallet{}.db3".format(i+1)
            os.remove(walletpath)
            wallet = UserWallet.Create(path=walletpath, password=mypassword)
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

            while Blockchain.Default().Height < 2:
                print("Waiting for wallet to sync...")
                time.sleep(1)

            #print("Wallet %s " % json.dumps(wallet.ToJson(), indent=4))

            if i == 0:
                print("Creating spend transaction to {}".format(to_addr))
                tx_json = self.begin_send(wallet, ['neo', to_addr, '100000000', multisig_addr])
                if tx_json is None:
                    break
            else:
                tx_json = self.sign_and_finish(wallet, tx_json)

            if tx_json == 'success':
                print("Finished, {} should now own all the NEO on the private network.".format(to_addr))
                break
            i += 1

        self.quit()


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: {} {{Address to receive all NEO}}".format(sys.argv[0]))
        sys.exit(1)

    pc = PrivnetClaimall()

    reactor.suggestThreadPoolSize(15)
    reactor.callInThread(pc.run)
    NodeLeader.Instance().Start()
    reactor.run()
