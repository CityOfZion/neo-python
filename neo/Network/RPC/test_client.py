from unittest import TestCase
from neo.Network.RPC.Client import RPCClient,RPCEnpoint
from neo.Core.Block import Block
from neo.Core.TX.Transaction import Transaction
import json
import binascii

from neo.UInt160 import UInt160
from neo.UInt256 import UInt256
from neo.Cryptography.Crypto import Crypto

class RPCClientTestCase(TestCase):


    sample_addr = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'

    sample_asset= 'c56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b'



    def test_client(self):

        client = RPCClient()

        self.assertIsNotNone(client.endpoints)

        self.assertGreater(len(client.endpoints), 0)

        self.assertIsInstance(client.default_enpoint, RPCEnpoint)

        self.assertEqual(client.default_enpoint.height, None)


    def test_client_setup(self):

        client = RPCClient(setup=True)

        self.assertIsNotNone(client.endpoints)

        self.assertGreater(len(client.endpoints), 0)

        self.assertIsInstance(client.default_enpoint, RPCEnpoint)

        self.assertIsNotNone(client.default_enpoint.height)

        self.assertEqual(client.default_enpoint.status, 200)

        client0 = client.default_enpoint
        client1 = client.endpoints[1]

#        self.assertGreaterEqual(client0.height, client1.height)




    def test_height(self):
        client = RPCClient()

        response = client.get_height()

        height = int(response)

        self.assertGreaterEqual(height, 0)


    def test_account_state(self):

        client = RPCClient()

        account = client.get_account(self.sample_addr)

        script_hash = bytearray(binascii.unhexlify(account['script_hash'][2:]))
        script_hash.reverse()

        self.assertEqual(len(script_hash), 20)

        uint = UInt160(data=script_hash)

        newaddr = Crypto.ToAddress(uint)

        self.assertEqual(newaddr, self.sample_addr)

        balances = account['balances']

        self.assertIsNotNone(balances)
        self.assertGreater(len(balances), 0)


    def test_asset_state(self):

        client = RPCClient()

        asset = client.get_asset(self.sample_asset)

        self.assertEqual(asset['type'], 'GoverningToken')

        self.assertEqual(int(asset['available']), 100000000 )

        self.assertEqual(int(asset['precision']), 0)


    def test_best_blockhash(self):

        client = RPCClient()

        hash = bytearray(binascii.unhexlify( client.get_best_blockhash()[2:]))
        hash.reverse()

        hash = UInt256(data=hash)

        self.assertIsNotNone(hash)


    def test_get_block_json(self):

        client = RPCClient()

        height = 12344
        blockjson1 = client.get_block(height)

        blockhash = blockjson1['hash'][2:]

        self.assertEqual(blockhash, '1e67372c158a4cfbb17b9ad3aaae77001a4247a00318e354c62e53b56af4006f')

        blockjson2 = client.get_block(blockhash)

        self.assertEqual(blockjson1, blockjson2)

        self.assertEqual(height, blockjson1['index'])


    def test_block_block(self):

        client = RPCClient()

        height = 12344

        block = client.get_block(height, as_json=False)

        self.assertIsInstance(block, Block)

        self.assertEqual(height, block.Index)

        self.assertEqual(block.Hash.ToString(),'1e67372c158a4cfbb17b9ad3aaae77001a4247a00318e354c62e53b56af4006f')


    def test_getblockhash(self):

        client = RPCClient()

        height = 12344

        hash = client.get_block_hash(height)

        self.assertEqual(hash[2:], '1e67372c158a4cfbb17b9ad3aaae77001a4247a00318e354c62e53b56af4006f')


    def test_sysfee(self):

        client = RPCClient()

        height = 740324

        fee = int(client.get_block_sysfee(height))

        self.assertEqual(fee, 469014)


    def test_contract_state(self):

        client = RPCClient()

        contract_hash = 'f8d448b227991cf07cb96a6f9c0322437f1599b9'

        contract = client.get_contract_state(contract_hash)

        hash = contract['hash'][2:]

        self.assertEqual(hash, contract_hash)


    def test_connection_count(self):

        client = RPCClient()

        connection_count = int(client.get_connection_count())

        self.assertGreater(connection_count, 0)

    def test_mempool(self):

        client = RPCClient()

        mempool = client.get_raw_mempool()

        self.assertIsInstance(mempool, list)


    def test_tx_json(self):

        client = RPCClient()

        hash = '58c634f81fbd4ae2733d7e3930a9849021840fc19dc6af064d6f2812a333f91d'
        tx = client.get_transaction(hash)

        self.assertEqual(tx['blocktime'],1510283768)

        self.assertEqual(tx['txid'][2:], hash)


    def test_tx_astx(self):
        client = RPCClient()

        hash = '58c634f81fbd4ae2733d7e3930a9849021840fc19dc6af064d6f2812a333f91d'
        tx = client.get_transaction(hash, as_json=False)

        self.assertIsInstance(tx, Transaction)

        self.assertEqual(tx.Hash.ToString(), hash)


    def test_get_storage(self):

        client = RPCClient()

        contract_hash = 'd7678dd97c000be3f33e9362e673101bac4ca654'
        key = 'totalSupply'

        storage = client.get_storage(contract_hash,key)

        self.assertIsInstance(storage, bytearray)

        intval = int.from_bytes(storage, 'little')

        self.assertEqual(intval, 196800000000000)


    def test_tx_out(self):

        client = RPCClient()

        tx_hash = '58c634f81fbd4ae2733d7e3930a9849021840fc19dc6af064d6f2812a333f91d'
        index = 0
        txout = client.get_tx_out(tx_hash, index)

        self.assertEqual(txout['asset'][2:],'602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7')
        self.assertEqual(txout['n'], index)
        self.assertEqual(txout['address'], self.sample_addr)


