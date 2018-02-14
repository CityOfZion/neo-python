from unittest import TestCase
from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.SmartContract.ApplicationEngine import ApplicationEngine

class GasCostTestCase(TestCase):


    _blockchain = None

    @classmethod
    def setUpClass(cls):

        print("Setting up class")
        Blockchain.DeregisterBlockchain()
        cls._blockchain = LevelDBBlockchain(path='./Chains/SC234')
        Blockchain.RegisterBlockchain(cls._blockchain)

        print("DEFAULT: %s " % Blockchain.Default())


    def test_script_one(self):
        script = b'01ab066b6579313233037075746780a1a5b87921dda4603b502ada749890cbca3434'

        engine = ApplicationEngine.Run(script)

        print("engine %s " % engine)
