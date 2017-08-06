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

        print("trying to deserialize coin ref")
        self.PrevHash = reader.ReadUInt256(reverse=False)
        print("sef prev hash: %s " % self.PrevHash )

        self.PrevIndex = reader.ReadUInt16()
        print("self prev index %s " % self.PrevIndex)

    def Serialize(self, writer):

        writer.WriteUInt256(self.PrevHash)
        writer.WriteUInt16(self.PrevIndex)

    def Equals(self, other):
        if other is None: return False
        if other.PrevHash == self.PrevHash and other.PrevIndex == self.PrevIndex: return True
        return False

    def ToJson(self):
        out = {
            'txid': self.PrevHash,
            'vout':self.PrevIndex
        }

        return json.dumps(out)