from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Wallets.utils import to_aes_key
from neo.Prompt.Commands.Wallet import AddAlias
from neo.Prompt.Utils import parse_param, lookup_addr_str
from neo.Core.Blockchain import Blockchain
from neocore.UInt160 import UInt160
from neocore.Fixed8 import Fixed8
from neocore.KeyPair import KeyPair
from neo.Wallets.NEP5Token import NEP5Token
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neo.Core.TX.Transaction import ContractTransaction, TransactionOutput
from neo.Network.NodeLeader import NodeLeader
import json
import binascii


class UserWalletTestCase(WalletFixtureTestCase):

    wallet_1_script_hash = UInt160(data=b'S\xefB\xc8\xdf!^\xbeZ|z\xe8\x01\xcb\xc3\xac/\xacI)')

    wallet_1_addr = 'APRgMZHZubii29UXF9uFa6sohrsYupNAvx'

    import_watch_addr = UInt160(data=b'\xaf\x12\xa8h{\x14\x94\x8b\xc4\xa0\x08\x12\x8aU\nci[\xc1\xa5')
    watch_addr_str = 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK'
    _wallet1 = None

    @property
    def GAS(self):
        return Blockchain.Default().SystemCoin().Hash

    @property
    def NEO(self):
        return Blockchain.Default().SystemShare().Hash

    @classmethod
    def GetWallet1(cls, recreate=False):
        if cls._wallet1 is None or recreate:
            cls._wallet1 = UserWallet.Open(UserWalletTestCase.wallet_1_dest(), to_aes_key(UserWalletTestCase.wallet_1_pass()))
        return cls._wallet1

    def test_0_bad_password(self):

        self.assertRaises(Exception, UserWallet.Open, UserWalletTestCase.wallet_1_dest(), to_aes_key('blah'))

    def test_1_initial_setup(self):

        wallet = self.GetWallet1()

        jsn = wallet.ToJson()

        addr = jsn['addresses'][0]

        self.assertEqual(self.wallet_1_addr, addr['script_hash'])

        balance_should_be = Fixed8.FromDecimal(100)

        gas_balance = wallet.GetBalance(self.GAS)

        self.assertEqual(balance_should_be, gas_balance)

        neo_balance = wallet.GetBalance(self.NEO)

        self.assertEqual(balance_should_be, neo_balance)

        self.assertEqual(wallet.WalletHeight, 750131)

    def test_2_transactions(self):

        wallet = self.GetWallet1()

        transactions = wallet.GetTransactions()

        self.assertEqual(2, len(transactions))

    def test_3_import_watch_addr(self):

        wallet = self.GetWallet1()

        wallet.AddWatchOnly(self.import_watch_addr)

        self.assertTrue(wallet.ContainsAddress(self.import_watch_addr))

        jsn = wallet.ToJson()

        all_addr = jsn['addresses']
        self.assertEqual(2, len(all_addr))

        found = False
        for addr in all_addr:

            if addr['script_hash'] == self.watch_addr_str:
                self.assertEqual(addr['is_watch_only'], True)
                found = True

        self.assertTrue(found)

        # now add it again

        self.assertRaises(Exception, wallet.AddWatchOnly, self.import_watch_addr)

    def test_4_get_change_address(self):

        wallet = self.GetWallet1()

        address = wallet.GetChangeAddress()

        self.assertEqual(address, self.wallet_1_script_hash)

    def test_5_export_wif(self):

        wallet = self.GetWallet1()

        keys = wallet.GetKeys()

        self.assertEqual(len(keys), 1)

        key = keys[0]

        wif = key.Export()

        self.assertEqual(wif, 'KzV2riT1Vqoi5th1uiCTN5adEtJwXevFxf7Nygant1sBaRfncmbz')

    def test_6_import_wif(self):

        wallet = self.GetWallet1()

        key_to_import = 'L3MBUkKU5kYg16KSZnqcaTj2pG5ei3fN9A4X7rxXys18GBDa3bH8'

        prikey = KeyPair.PrivateKeyFromWIF(key_to_import)
        keypair = wallet.CreateKey(prikey)

        key_out = keypair.PublicKey.encode_point(True).decode('utf-8')

        self.assertEqual(key_out, '03f3a3b5a4d873933fc7f4b53113e8eb999fb20038271fbbb10255585670c3c312')

    def test_7_import_token(self):

        wallet = self.GetWallet1()

        token_hash = b'f8d448b227991cf07cb96a6f9c0322437f1599b9'
        contract = Blockchain.Default().GetContract(token_hash)

        token = NEP5Token(binascii.hexlify(contract.Code.Script))
        token.Query()

        self.assertEqual(token.name, 'NEP5 Standard')
        self.assertEqual(token.decimals, 8)
        self.assertEqual(token.symbol, 'NEP5')

        wallet.AddNEP5Token(token)

        self.assertEqual(len(wallet.GetTokens()), 1)

    def test_8_named_addr(self):

        wallet = self.GetWallet1()

        AddAlias(wallet, self.wallet_1_addr, 'my_named_addr')

        named = [n.Title for n in wallet.NamedAddr]

        self.assertIn('my_named_addr', named)

        param = 'my_named_addr'

        addr = lookup_addr_str(wallet, param)

        self.assertIsInstance(addr, UInt160)

        self.assertEqual(addr, self.wallet_1_script_hash)

        presult = parse_param(param, wallet)

        self.assertIsInstance(presult, bytearray)

        self.assertEqual(presult, self.wallet_1_script_hash.Data)

    def test_9_send_neo_tx(self):

        wallet = self.GetWallet1()

        tx = ContractTransaction()
        tx.outputs = [TransactionOutput(Blockchain.SystemShare().Hash, Fixed8.FromDecimal(10.0), self.import_watch_addr)]

        tx = wallet.MakeTransaction(tx)

        cpc = ContractParametersContext(tx)
        wallet.Sign(cpc)
        tx.scripts = cpc.GetScripts()

        result = NodeLeader.Instance().Relay(tx)
        self.assertEqual(result, True)
