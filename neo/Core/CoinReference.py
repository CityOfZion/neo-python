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
        print("serializing coin reference")
        writer.WriteUInt256(self.PrevHash)
        writer.WriteUInt16(self.PrevIndex)

    def Equals(self, other):
        if other is None: return False
        if other.PrevHash == self.PrevHash and other.PrevIndex == self.PrevIndex: return True
        return False

    def ToJson(self):
        out = {
            'txid': self.PrevHash.ToString(),
            'vout':self.PrevIndex
        }

        return out