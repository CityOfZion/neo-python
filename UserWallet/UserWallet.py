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


# Test Params
privateKey = '86f9c92cb1925f53df65c5638c165acb9e13fb4591f4d65c988393372f8b8572'
target_priv = 'd07019bd2bf82846c390b176b75324c4f26c0e4562e7f2f58897fd283cefb8ca'

prevHash = '358d4866a19367d01bf41ace55dd50fb4a9fbfa44aa6dce2524107de4588d98b'
value = '100'

# Get Account
a = Account(privateKey)
print 'PrivateKey ->', a.privateKey
print 'PublicKey ->', a.publicKey
print 'ScriptHash ->', a.scriptHash
print 'Address ->', a.address

c = Contract()
c.createSignatureContract(a.publicKey)
print 'RedeemScipt ->', c.redeemScript


b = Account(target_priv)
print 'Target Address ->', b.address

# Create Outputs
Outputs = [TransactionOutput(
            AssetId='f252a09a24591e8da31deec970871cc7678cb55023db049551e91f7bac28e27b',
            Value=value,
            ScriptHash=a.scriptHash)]

# Create Inputs

Inputs = [TransactionInput(
            prevHash=prevHash,
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
print 'TXID ->',tx.ensureHash()

Redeem_script = c.redeemScript

# Signature

from ecdsa import SigningKey, NIST256p
sk = SigningKey.from_string(binascii.unhexlify(a.privateKey), curve=NIST256p, hashfunc=hashlib.sha256)
signature = binascii.hexlify(sk.sign(binascii.unhexlify(reg_tx),hashfunc=hashlib.sha256))
regtx = reg_tx + '014140' + signature + '23' + Redeem_script

# sendRawTransaction

node = RemoteNode(url='http://10.84.136.112:20332')
# print node.getBestBlockhash()
print 'Return Info from RPC:',
print node.sendRawTransaction(regtx)
# print node.getRawTransaction('a353175d2e5fdd97fa34536727b322e2a582cfd280db9e07163c259b04277b0e')
# time.sleep(20)
