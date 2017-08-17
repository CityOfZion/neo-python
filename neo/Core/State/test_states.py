
import unittest

from neo.Core.State.SpentCoinState import SpentCoinState

from neo.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream

import binascii

class StateTestCase(unittest.TestCase):


    key = b'617cafec2da972f17afc66b1b30b412539a5e3caa9f74afadcbd45b7a1dae5a7'
    buffer = b'007cafec2da972f17afc66b1b30b412539a5e3caa9f74afadcbd45b7a1dae5a7006121a40201000025a40200'

    def test_spentcoin(self):


        #the key and buffer from above are possibly not correct
        #should log a sample value from the C# version and see what an example buffer would be

        input = binascii.unhexlify(self.buffer)

        ms = MemoryStream(input)
        reader = BinaryReader(ms)

        spentcoin = SpentCoinState.DeserializeFromDB(input)

