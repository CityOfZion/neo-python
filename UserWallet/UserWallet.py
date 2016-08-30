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
from AntShares.Core.Helper import *

from AntShares.Core.TransactionOutput import TransactionOutput
from AntShares.IO.MemoryStream import MemoryStream
from AntShares.IO.BinaryWriter import BinaryWriter

# Create Outputs
Outputs = [TransactionOutput(
            AssetId='f252a09a24591e8da31deec970871cc7678cb55023db049551e91f7bac28e27b',
            Value='100',
            ScriptHash='9c17b4ee1441676e36d77a141dd77869d271381d')]





stream = MemoryStream()
writer = BinaryWriter(stream)
Outputs.serialize(writer)
print stream.toArray()
