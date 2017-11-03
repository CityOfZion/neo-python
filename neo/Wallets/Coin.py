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
from neo.Core.State.CoinState import CoinState
from neo.IO.Mixins import TrackableMixin
from neo.Cryptography.Crypto import Crypto


class Coin(TrackableMixin):

    Output = None
    Reference = None

    _address = None
    _state = CoinState.Unconfirmed

    @staticmethod
    def CoinFromRef(coin_ref, tx_output, state=CoinState.Unconfirmed):
        coin = Coin(coin_reference=coin_ref, tx_output=tx_output, state=state)
        return coin

    def __init__(self, prev_hash=None, prev_index=None, tx_output=None, coin_reference=None, state=CoinState.Unconfirmed):
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
        if self._address is None:
            self._address = Crypto.ToAddress(self.TXOutput.ScriptHash)
        return self._address

    @property
    def State(self):
        return self._state

    @State.setter
    def State(self, value):
        self._state = value

    def Equals(self, other):
        if other is None or other is not self:
            return False
        return True

    def ToJson(self):
        return {
            'Reference': self.Reference.ToJson(),
            'Output': self.Output.ToJson()
        }
