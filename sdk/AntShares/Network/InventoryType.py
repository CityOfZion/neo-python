# -*- coding:utf-8 -*-
"""
Description:
    Inventory Type
Usage:
    from AntShares.Network.InventoryType import InventoryType
"""


class InventoryType(object):
    TX = 0x01         # Transaction
    Block = 0x02      # Block
    Consensus = 0xe0  # Consensus information
