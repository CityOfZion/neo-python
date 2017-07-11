# -*- coding: UTF-8 -*-

import sys
import json

class CoinReference(object):

    PrevHash = None

    PrevIndex = None

    def __init__(self, prev_hash=None, prev_index=None):
        self.PrevHash = prev_hash
        self.PrevIndex = prev_index

    def Size(self):
        return sys.getsizeof(self.PrevHash) + sys.getsizeof(int)

    def Deserialize(self, reader):

        self.PrevHash = reader.readUInt256()
        self.PrevIndex = reader.readUInt16()

    def Serialize(self, writer):
        writer.writeUInt256(self.PrevHash)
        writer.writeUInt16(self.PrevIndex)

    def ToJson(self):
        out = {
            'txid': self.PrevHash,
            'vout':self.PrevIndex
        }

        return json.dumps(out)