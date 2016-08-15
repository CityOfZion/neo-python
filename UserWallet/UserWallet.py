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

import AntShares


# # Create Outputs
# Outpus = AntShares.Core.TransactionOutput(assetid='f252a09a24591e8da31deec970871cc7678cb55023db049551e91f7bac28e27b',
#                                           value='100',
#                                           scripthash='')
