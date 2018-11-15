from neo.Utils.WalletFixtureTestCase import WalletFixtureTestCase
from neo.Wallets.utils import to_aes_key
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
import shutil
from neo.Prompt.Commands.LoadSmartContract import LoadContract, GatherLoadedContractParams, ImportMultiSigContractAddr
import mock


class LoadSmartContractTestCase(WalletFixtureTestCase):

    wallet_1_addr = "AJQ6FoaSXDFzA6wLnyZ1nFN7SGSN2oNTc3"
    wallet_1_pk = "03cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c6"

    _wallet1 = None

    wallet_2_pk = "03c46aec8d1ac8cb58fe74764de223d15e7045de67a51d1a4bcecd396918e96034"

    @classmethod
    def GetWallet1(cls, recreate=False):
        if cls._wallet1 is None or recreate:
            shutil.copyfile(cls.wallet_1_path(), cls.wallet_1_dest())
            cls._wallet1 = UserWallet.Open(LoadSmartContractTestCase.wallet_1_dest(),
                                           to_aes_key(LoadSmartContractTestCase.wallet_1_pass()))
        return cls._wallet1

    def test_loadcontract(self):

        # test too few args
        args = []

        res = LoadContract(args)

        self.assertFalse(res)

        # test for void (ff) type in params
        with self.assertRaises(ValueError) as e:
            args = ["path", "07ff10", "01", "False", "False", "False"]

            LoadContract(args)

        self.assertTrue("Void is not a valid input parameter type" in str(e.exception))

        # test for .py in path
        args = ["path.py", "070710", "01", "False", "False", "False"]

        res = LoadContract(args)

        self.assertFalse(res)

        # test good contract
        with mock.patch("builtins.open", mock.mock_open(read_data="path.avm")):

            args = ["path.avm", "070710", "01", "True", "True", "True"]

            res = LoadContract(args)

        self.assertTrue(res)

        # test if a file is not found
        with mock.patch("builtins.open", new_callable=mock.mock_open) as mo:
            mock_file = mo.return_value
            mock_file.read.side_effect = None

            args = ["path.avm", "070710", "01", "False", "False", "False"]

            res = LoadContract(args)

        self.assertTrue(res is None)

        # test params exception
        with mock.patch("builtins.open", mock.mock_open(read_data="path.avm")):
            with mock.patch("neo.Prompt.Commands.LoadSmartContract.binascii", return_value=TypeError):

                args = ["path.avm", "070710", "01", "False", "False", "False"]

                res = LoadContract(args)

        self.assertTrue(res)

        # test params exception
        with mock.patch("builtins.open", mock.mock_open(read_data="path.avm")):
            with mock.patch("builtins.bytearray", return_value=TypeError):

                args = ["path.avm", "070710", "01", "False", "False", "False"]

                res = LoadContract(args)

        self.assertTrue(res)

    def test_gatherloadedcontractparams(self):

        # test too few args
        with self.assertRaises(Exception) as e:
            args = []
            script = "script"

            GatherLoadedContractParams(args, script)

        self.assertTrue("please specify contract properties like {params} {return_type} {needs_storage} {needs_dynamic_invoke} {is_payable}" in str(e.exception))

        # test for void (ff) type in params
        with self.assertRaises(ValueError) as e:
            args = ["07ff10", "01", "False", "False", "False"]
            script = b"script"

            GatherLoadedContractParams(args, script)

        self.assertTrue("Void is not a valid input parameter type" in str(e.exception))

        # test good params with needs_dynamic_invoke
        with mock.patch("neo.Prompt.Commands.LoadSmartContract.generate_deploy_script", return_value=True):
            args = ["070710", "01", "False", "True", "False"]
            script = "script"

            res = GatherLoadedContractParams(args, script)

        self.assertTrue(res)

    def test_importmultisigcontractaddr(self):

        # good test
        wallet = self.GetWallet1(recreate=True)
        args = [self.wallet_1_pk, 2, self.wallet_1_pk, self.wallet_2_pk]

        address = ImportMultiSigContractAddr(wallet, args)

        self.assertEqual(address[0], "A")
        self.assertEqual(len(address), 34)

        # test too few args
        wallet = self.GetWallet1()
        args = [self.wallet_1_pk, 2, self.wallet_1_pk]  # need at least four args

        res = ImportMultiSigContractAddr(wallet, args)

        self.assertFalse(res)

        # test no wallet
        wallet = None
        args = [self.wallet_1_pk, 2, self.wallet_1_pk, self.wallet_2_pk]

        res = ImportMultiSigContractAddr(wallet, args)

        self.assertFalse(res)

        # test bad first pk
        with self.assertRaises(Exception) as e:
            wallet = self.GetWallet1(recreate=True)
            args = [self.wallet_2_pk, 2, self.wallet_1_pk, self.wallet_2_pk]  # first pk needs to be from wallet

            ImportMultiSigContractAddr(wallet, args)

        self.assertTrue("Invalid operation - public key mismatch" in str(e.exception))

        # test bad second pk
        wallet = self.GetWallet1(recreate=True)
        args = [self.wallet_1_pk, 2, "03cbb45da6072c14761c9da545749d9cfd863f860c351066d16df480602a2024c", self.wallet_2_pk]  # pk is too short

        res = ImportMultiSigContractAddr(wallet, args)

        self.assertFalse(res)

        # test minimum # of signatures required < 1
        args = [self.wallet_1_pk, 0, self.wallet_1_pk, self.wallet_2_pk]

        res = ImportMultiSigContractAddr(wallet, args)

        self.assertFalse(res)

        # test minimum # of signatures required > len(publicKeys)
        args = [self.wallet_1_pk, 3, self.wallet_1_pk, self.wallet_2_pk]

        res = ImportMultiSigContractAddr(wallet, args)

        self.assertFalse(res)
