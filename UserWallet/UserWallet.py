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
from AntShares.IO.MemoryStream import MemoryStream
from AntShares.IO.BinaryWriter import BinaryWriter

from AntShares.Wallets.Wallet import *

# Create Outputs
Outputs = [TransactionOutput(
            AssetId='f252a09a24591e8da31deec970871cc7678cb55023db049551e91f7bac28e27b',
            Value='100',
            ScriptHash='9c17b4ee1441676e36d77a141dd77869d271381d')]

# """
# # Test Serialize TransactionOutput
#
# stream = MemoryStream()
# writer = BinaryWriter(stream)
# Outputs[0].serialize(writer)
# print stream.toArray()
# """

outputs = [{'Asset': u'AntCoin',
            'Value': u'100',
            'Scripthash': u'9c17b4ee1441676e36d77a141dd77869d271381d'}]

inputs, coins, outputs = selectInputs(getInputs(), outputs)

Inputs = [TransactionInput(
            prevHash=inputs[0][0].split('-')[0],
            prevIndex=inputs[0][0].split('-')[1])]

# # Test Serialize TransactionInput
#
# stream = MemoryStream()
# writer = BinaryWriter(stream)
# Inputs[0].serialize(writer)
# print stream.toArray()

tx = Transaction(Inputs, Outputs)

# Test Serialize Transaction

stream = MemoryStream()
writer = BinaryWriter(stream)
tx.serialize(writer)
print stream.toArray()
