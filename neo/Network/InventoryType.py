"""
Description:
    Inventory Type
Usage:
    from neo.Network.InventoryType import InventoryType
"""


class InventoryType:
    TX = b'\x01'  # Transaction
    Block = b'\x02'  # Block
    Consensus = b'\xe0'  # Consensus information

    TXInt = 1
    BlockInt = 2
    ConsensusInt = 224

    @staticmethod
    def AllInventoriesInt():
        """
        Get all inventory types as ints.

        Returns:
            list: of int formatted inventory types.
        """
        return [1, 2, 224]
