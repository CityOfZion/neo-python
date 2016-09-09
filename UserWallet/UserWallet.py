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
from AntShares.Helper import *


from AntShares.Wallets.Account import Account
from AntShares.Wallets.Contract import Contract

# Creat Account

# privateKey = '7d989d02dff495cc1bbc35e891c153b98781e015a20ce276b86afc7856f85efa'
privateKey = 'd64a2e1acf97ed7befaa3af29f43d6f0512647a627d7285a69437ea6980ff352'


a = Account(privateKey)
print 'PrivateKey ->', a.privateKey
print 'PublicKey ->', a.publicKey
print 'ScriptHash ->', a.scriptHash
print 'Address ->', a.address

c = Contract()
c.createSignatureContract(a.publicKey)
print 'RedeemScipt ->', c.redeemScript

target_priv = 'd07019bd2bf82846c390b176b75324c4f26c0e4562e7f2f58897fd283cefb8ca'
b = Account(target_priv)

# Create Outputs
Outputs = [TransactionOutput(
            AssetId='f252a09a24591e8da31deec970871cc7678cb55023db049551e91f7bac28e27b',
            Value='100.0',
            ScriptHash=b.scriptHash)]

# Create Inputs

Inputs = [TransactionInput(
            prevHash='10fd476b557d6347aa910e2ff57a2867479d4116b1d99838926d4bd3dc4bffb8',
            prevIndex=0)]

# Make RegisterTransaction
Issuer = a.publicKey
Admin = a.scriptHash
# tx = RegisterTransaction(Inputs, Outputs, 0x60, '测试资产注册', -0.00000001, Issuer, Admin)
tx = Transaction(Inputs, Outputs)

stream = MemoryStream()
writer = BinaryWriter(stream)
tx.serializeUnsigned(writer)
reg_tx = stream.toArray()

print 'TX ->', repr(reg_tx)



Redeem_script = c.redeemScript

# Signature

from ecdsa import SigningKey, NIST256p
sk = SigningKey.from_string(binascii.unhexlify(a.privateKey), curve=NIST256p, hashfunc=hashlib.sha256)
signature = binascii.hexlify(sk.sign(binascii.unhexlify(reg_tx),hashfunc=hashlib.sha256))
regtx = reg_tx + '014140' + signature + '23' + Redeem_script

# sendRawTransaction

node = RemoteNode(url='http://47.90.66.157:20332')
# print node.getBestBlockhash()
print 'Return Info from RPC:',
print node.sendRawTransaction(regtx)
# print node.getRawTransaction('82b643948ba8daeecbb228923206c7ff91bd0b893020336a19d4995134d9689f')
# time.sleep(20)
