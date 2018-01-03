# -*- coding:utf-8 -*-
"""
Description:
    Inventory Type
Usage:
    from neo.Network.InventoryType import InventoryType
"""


class InventoryType(object):
    TX = b'\x01'  # Transaction
    Block = b'\x02'  # Block
    Consensus = b'\xe0'  # Consensus information

    @staticmethod
    def AllInventoriesInt():
        """
        Get all inventory types as ints.

        Returns:
            list: of int formatted inventory types.
        """
        return [int.from_bytes(InventoryType.TX, 'little'),
                int.from_bytes(InventoryType.Block, 'little'),
                int.from_bytes(InventoryType.Consensus, 'little')]
