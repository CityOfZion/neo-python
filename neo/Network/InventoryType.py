# -*- coding:utf-8 -*-
"""
Description:
    Inventory Type
Usage:
    from neo.Network.InventoryType import InventoryType
"""


class InventoryType(object):
    TX = b'\x01'         # Transaction
    Block = 'b\x02'      # Block
    Consensus = 'b\xe0'  # Consensus information
