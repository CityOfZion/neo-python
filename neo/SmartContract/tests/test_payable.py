from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Prompt.Commands.BuildNRun import DoRun
from neo.Wallets.utils import to_aes_key
import binascii


class SmartContractPayable(WalletFixtureTestCase):

    _wallet1 = None
    _path = "neo/SmartContract/tests/PayableTest.avm"

    @classmethod
    def GetWallet1(cls, recreate=False):
        if cls._wallet1 is None or recreate:
            cls._wallet1 = UserWallet.Open(SmartContractPayable.wallet_1_dest(), to_aes_key(SmartContractPayable.wallet_1_pass()))
        return cls._wallet1

    def test_is_payable(self):
        """
        Result [{'type': 'Boolean', 'value': True}]
        """

        wallet = self.GetWallet1()

        arguments = [self._path, "False", "False", "True", "07", "01", "payable"]

        with open(self._path, 'rb') as f:

            content = f.read()

            try:
                content = binascii.unhexlify(content)
            except Exception as e:
                pass

            script = content

        tx, result, total_ops, engine = DoRun(script, arguments, wallet, self._path)

        self.assertTrue(result[0].GetBoolean())

    def test_is_not_payable(self):
        """
        Result [{'type': 'Boolean', 'value': False}]
        """

        wallet = self.GetWallet1()

        arguments = [self._path, "False", "False", "False", "07", "01", "payable"]

        with open(self._path, 'rb') as f:

            content = f.read()

            try:
                content = binascii.unhexlify(content)
            except Exception as e:
                pass

            script = content

        tx, result, total_ops, engine = DoRun(script, arguments, wallet, self._path)

        self.assertFalse(result[0].GetBoolean())
