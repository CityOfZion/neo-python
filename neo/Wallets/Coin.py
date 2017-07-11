# -*- coding:utf-8 -*-
"""
Description:
    define the data struct of coin
Usage:
    from neo.Wallets.Coin import Coin
"""

from neo.Core.TX.Transaction import TransactionOutput
from neo.Core.CoinReference import CoinReference
from neo.Wallets import Wallet
from neo.Core.CoinState import CoinState
from neo.IO.Mixins import TrackableMixin
from neo.IO.TrackState import TrackState

class Coin(TrackableMixin):

    TXOutput = None
    CoinRef = None

    _address = None
    _state = CoinState.Unconfirmed

    TrackingState = TrackState.NoState


    @staticmethod
    def CoinFromRef(coin_ref, tx_output, state=CoinState.Unconfirmed):
        coin = Coin(tx_output=tx_output)
        coin.CoinRef = coin_ref
        coin._state = state
        return coin

    def __init__(self, prev_hash=None, prev_index=None, tx_output=None, state=CoinState.Unconfirmed):
        self.CoinRef = CoinReference(prev_hash, prev_index)
        self.TXOutput = tx_output
        self._state = state


    @property
    def Address(self):
        if self._address is None:
            self._address = Wallet.ToAddress(self.TXOutput.ScriptHash)
        return self._address

    @property
    def State(self):
        return self._state

    @State.setter
    def State(self,value):
        if self._state != value:
            self._state = value
            if self.TrackingState == TrackState.NoState:
                self.TrackingState = TrackState.Changed



    def Equals(self, other):
        if other is None or other is not self: return False
        return True

