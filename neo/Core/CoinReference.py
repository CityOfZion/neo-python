# -*- coding: UTF-8 -*-

import sys
import json
import binascii


class CoinReference(object):

    PrevHash = None

    PrevIndex = None

    def __init__(self, prev_hash=None, prev_index=None):
        self.PrevHash = prev_hash
        self.PrevIndex = prev_index

    def Size(self):
        return sys.getsizeof(self.PrevHash) + sys.getsizeof(int)

    def Deserialize(self, reader):

        self.PrevHash = reader.ReadUInt256()
        self.PrevIndex = reader.ReadUInt16()

    def Serialize(self, writer):
        writer.WriteUInt256(self.PrevHash)
        writer.WriteUInt16(self.PrevIndex)

    def Equals(self, other):
        if other is None:
            return False
        if other.PrevHash.ToBytes() == self.PrevHash.ToBytes() and other.PrevIndex == self.PrevIndex:
            return True
        return False

    def __eq__(self, other):
        if other is None:
            return False
        if other.PrevHash.ToBytes() == self.PrevHash.ToBytes() and other.PrevIndex == self.PrevIndex:
            return True
        return False

    def __hash__(self):
        return int.from_bytes(self.PrevHash.ToBytes(), 'little') + self.PrevIndex

    def ToJson(self):
        out = {
            'txid': self.PrevHash.ToString(),
            'vout': self.PrevIndex
        }

        return out
