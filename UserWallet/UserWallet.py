# -*- coding:utf-8 -*-
"""
Description:
    UserWallet
"""


from bitcoin import *
from ecdsa import SigningKey, NIST256p

import binascii
import hashlib
import sys
import os

# ../sdk/
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sdk'))

from AntShares.Network.RemoteNode import RemoteNode

from AntShares.Core.TransactionOutput import TransactionOutput
from AntShares.Core.TransactionInput import TransactionInput
from AntShares.Core.Transaction import Transaction
from AntShares.Core.RegisterTransaction import RegisterTransaction
from AntShares.IO.MemoryStream import MemoryStream
from AntShares.IO.BinaryWriter import BinaryWriter

from AntShares.Wallets.Wallet import *
from AntShares.Wallets.Coin import Coin 
from AntShares.Wallets.CoinState import CoinState 
from AntShares.Helper import *


from AntShares.Wallets.Account import Account
from AntShares.Wallets.Contract import Contract
from AntShares.Implementations.Wallets.IndexedDBWallet import IndexedDBWallet

def pay(payer_id,payees,asset):
    wallet_db = IndexedDBWallet()
    # step 1: get payer account
    payer = wallet_db.queryAccount(work_id=payer_id)
    if payer == None:
        print '%s : not exist payer block chain account' % payer_id
        return 2
    payer_acc = Account(payer['pri_key'])
    contract = Contract()
    contract.createSignatureContract(payer_acc.publicKey)

    # step 2: load payer available coins 
    coins = wallet_db.loadCoins(address=payer['address'],asset=asset)

    # step 3: select coins
    wallet = Wallet()
    selected_coins = wallet.selectCoins(coins,payees)
    if len(selected_coins) == 0:
        print 'no enough coins'
        return 5
    change = sum([int(c.value) for c in selected_coins]) - sum([int(p['amount']) for p in payees]) 

    # step 4: construct outputs 
    outputs = []
    payee_accs = {}
    for p in payees:
        payee = wallet_db.queryAccount(work_id=p['work_id'])
        if payee == None:
            print '%s : not exist payee block chain account' % payer_id
            return 3
        acc = Account(payee['pri_key'])
        output = TransactionOutput(AssetId=asset,Value=p['amount'],ScriptHash=acc.scriptHash)
        outputs.append(output)
        payee_accs[acc.scriptHash] = acc
    # add change output
    if change > 0:
        outputs.append(TransactionOutput(AssetId=asset,Value=change,ScriptHash=payer_acc.scriptHash))
        payee_accs[payer_acc.scriptHash] = payer_acc

    # step 5: construct inputs
    inputs = [TransactionInput(prevHash=c.txid, prevIndex=c.idx) for c in selected_coins]

    # step 6: make transaction
    tx = Transaction(inputs, outputs)
    stream = MemoryStream()
    writer = BinaryWriter(stream)
    tx.serializeUnsigned(writer)
    reg_tx = stream.toArray()
    txid = tx.ensureHash()
    print 'TX ->', repr(reg_tx)
    print 'TXID ->',txid

    # step 7: Signature
    Redeem_script = contract.redeemScript
    sk = SigningKey.from_string(binascii.unhexlify(payer_acc.privateKey), curve=NIST256p, hashfunc=hashlib.sha256)
    signature = binascii.hexlify(sk.sign(binascii.unhexlify(reg_tx),hashfunc=hashlib.sha256))
    regtx = reg_tx + '014140' + signature + '23' + Redeem_script

    # step 8: sendRawTransaction
    node = RemoteNode(url='http://10.84.136.112:20332')
    response = node.sendRawTransaction(regtx)

    # step 9: update coin status
    if response['result'] == True:
        incoming = []
        for i in range(len(outputs)):
            coin = Coin(txid=txid, idx=i, value=outputs[i].Value, asset=asset, address=payee_accs[outputs[i].ScriptHash].address,status=CoinState.Unconfirmed)
            incoming.append(coin)
        wallet_db.onSendTransaction(spending=selected_coins,incoming=incoming)
        return 0
    else:
        return 6

def create_accoount():
    pass

def __test():
    payer = 'test11'
    payees = [{'work_id':'sys','amount':100},{'work_id':'vote_temp','amount':200}]
    asset = 'dc3d9da12d13a4866ced58f9b611ad0d1e9d5d2b5b1d53021ea55a37d3afb4c9'
    pay(payer_id=payer,payees=payees,asset=asset)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        if sys.argv[1] == 'test':
            __test()
        elif sys.argv[1] == '':
            pass
        else:
            print 'error params'
    else:
        pass


