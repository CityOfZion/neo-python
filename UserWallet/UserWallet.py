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
from AntShares.Core.IssueTransaction import IssueTransaction
from AntShares.IO.MemoryStream import MemoryStream
from AntShares.IO.BinaryWriter import BinaryWriter

from AntShares.Wallets.Wallet import *
from AntShares.Wallets.Coin import Coin
from AntShares.Wallets.CoinState import CoinState
from AntShares.Helper import *


from AntShares.Wallets.Account import Account
from AntShares.Wallets.Contract import Contract
from AntShares.Implementations.Wallets.IndexedDBWallet import IndexedDBWallet

def makeIssueTransaction(privKey, Outputs):

    payer_acc = Account(privKey)
    contract = Contract()
    contract.createSignatureContract(payer_acc.publicKey)

    # step 5: construct inputs
    inputs = []

    # step 6: make transaction
    tx = IssueTransaction(inputs, Outputs)
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
    print response

def pay(payer_id, payees, asset):
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
    selected_coins = wallet.selectCoins(coins, payees)
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
        output = TransactionOutput(AssetId=asset, Value=p['amount'], ScriptHash=acc.scriptHash)
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

def __test():
    payer = 'test11'
    payees = [{'work_id':'sys','amount':100},{'work_id':'vote_temp','amount':200}]
    asset = 'dc3d9da12d13a4866ced58f9b611ad0d1e9d5d2b5b1d53021ea55a37d3afb4c9'
    pay(payer_id=payer, payees=payees, asset=asset)

def __testIssueTransaction():
    privKey = '86f9c92cb1925f53df65c5638c165acb9e13fb4591f4d65c988393372f8b8572'
    asset = '7bc3daf1c4484483d5aeb7729c7cc9c65c19dc323c487390d435f06ebe7bb0c5'
    outputs = [TransactionOutput(AssetId=asset, Value='1000', ScriptHash='58d7cfe812133ca2db83b312222b9384ce08366f'),
               TransactionOutput(AssetId=asset, Value='1000', ScriptHash='3f36d431358296ffb50d131e952ab35a74331716')]
    makeIssueTransaction(privKey, outputs)

def __testMakeTransaction():
    wallet_db = IndexedDBWallet()
    # step 1: get payer account
    privKey = '86f9c92cb1925f53df65c5638c165acb9e13fb4591f4d65c988393372f8b8572'

    payer_acc = Account(privKey)
    contract = Contract()
    contract.createSignatureContract(payer_acc.publicKey)

    asset = 'f252a09a24591e8da31deec970871cc7678cb55023db049551e91f7bac28e27b'

    coins = wallet_db.loadCoins(address=payer_acc.address,asset=asset)

    wallet = Wallet()


    inputs = []
    outputs = [TransactionOutput(AssetId=asset, Value='70', ScriptHash='58d7cfe812133ca2db83b312222b9384ce08366f'),
               TransactionOutput(AssetId=asset, Value='50', ScriptHash='3f36d431358296ffb50d131e952ab35a74331716')]
    tx = Transaction(inputs, outputs)
    wallet.makeTransaction(tx, payer_acc)



if __name__ == '__main__':
    if len(sys.argv) == 2:
        if sys.argv[1] == 'test':
            __test()
        elif sys.argv[1] == 'testIssue':
            __testIssueTransaction()
        elif sys.argv[1] == 'testMake':
            __testMakeTransaction()
        else:
            print 'error params'
    else:
        print 'python UserWallet.py test for __test()'
