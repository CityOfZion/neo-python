
from .VersionPayload import VersionPayload
from neo.Network.Message import Message
from neo.IO.Helper import AsSerializableWithType
from neo.IO.BinaryWriter import BinaryWriter
from neo.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream
from neo import Settings
from neo.Core.Helper import Helper
import random
import unittest
import binascii


class PayloadTestCase(unittest.TestCase):

    port = 20333
    nonce = random.randint(12949672,42949672)
    ua = "/NEO:2.0.1/"

    payload = None
    def setUp(self):


        self.payload = VersionPayload(self.port, self.nonce, self.ua)
