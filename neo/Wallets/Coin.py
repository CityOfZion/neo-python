# -*- coding:utf-8 -*-
"""
Description:
    define the data struct of coin
Usage:
    from neo.Wallets.Coin import Coin
"""
from neo.Core.CoinReference import CoinReference
from neo.Core.State.CoinState import CoinState
from neocore.IO.Mixins import TrackableMixin
from neocore.Cryptography.Crypto import Crypto


class Coin(TrackableMixin):
    Output = None
    Reference = None

    _address = None
    _state = CoinState.Unconfirmed

    @staticmethod
    def CoinFromRef(coin_ref, tx_output, state=CoinState.Unconfirmed):
        """
        Get a Coin object using a CoinReference.

        Args:
            coin_ref (neo.Core.CoinReference): an object representing a single UTXO / transaction input.
            tx_output (neo.Core.Transaction.TransactionOutput): an object representing a transaction output.
            state (neo.Core.State.CoinState):

        Returns:
            Coin: self.
        """
        coin = Coin(coin_reference=coin_ref, tx_output=tx_output, state=state)
        return coin

    def __init__(self, prev_hash=None, prev_index=None, tx_output=None, coin_reference=None,
                 state=CoinState.Unconfirmed):
        """
        Create an instance.

        Args:
            prev_hash (neocore.UInt256): (Optional if coin_reference is given) the hash of the previous transaction.
            prev_index (UInt16/int): (Optional if coin_reference is given) index of the previous transaction.
            tx_output (neo.Core.Transaction.TransactionOutput): an object representing a transaction output.
            coin_reference (neo.Core.CoinReference): (Optional if prev_hash and prev_index are given) an object representing a single UTXO / transaction input.
            state (neo.Core.State.CoinState):
        """
        if prev_hash and prev_index:
            self.Reference = CoinReference(prev_hash, prev_index)
        elif coin_reference:
            self.Reference = coin_reference
        else:
            self.Reference = None
        self.Output = tx_output
        self._state = state

    @property
    def Address(self):
        """
        Get the wallet address associated with the coin.

        Returns:
            str: base58 encoded string representing the wallet address.
        """
        if self._address is None:
            self._address = Crypto.ToAddress(self.TXOutput.ScriptHash)
        return self._address

    @property
    def State(self):
        """
        Get the coin state.

        Returns:
            neo.Core.State.CoinState: the coins state.
        """
        return self._state

    @State.setter
    def State(self, value):
        """
        Set the coin state.

        Args:
            value (neo.Core.State.CoinState): the new coin state.
        """
        self._state = value

    def Equals(self, other):
        """
        Compare `other` to self.

        Args:
            other (object):

        Returns:
            True if object is equal to self. False otherwise.
        """
        if other is None or other is not self:
            return False
        return True

    def RefToBytes(self):
        vin_index = bytearray(self.Reference.PrevIndex.to_bytes(1, 'little'))
        vin_tx = self.Reference.PrevHash.Data
        vindata = vin_tx + vin_index
        return vindata

    def ToJson(self):
        """
        Convert object members to a dictionary that can be parsed as JSON.

        Returns:
             dict:
        """
        return {
            'Reference': self.Reference.ToJson(),
            'Output': self.Output.ToJson(index=0),
        }
