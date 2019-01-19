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
        # test for void (ff) type in params
        with self.assertRaises(ValueError) as e:
            LoadContract("path", False, False, False, "07ff10", "01")

        self.assertTrue("Void is not a valid input parameter type" in str(e.exception))

        # test for .py in path
        with self.assertRaises(ValueError) as e:
            res = LoadContract("path.py", False, False, False, "070710", "01")
            self.assertFalse(res)
        self.assertTrue("Please load a compiled .avm file" in str(e.exception))

        # test if a file is not found
        with mock.patch("builtins.open", new_callable=mock.mock_open) as mo:
            with self.assertRaises(Exception) as context:
                mock_file = mo.return_value
                mock_file.read.side_effect = None

                res = LoadContract("path.avm", False, False, False, "070710", "01")

                self.assertIn("Error loading contract for path", str(context.exception))
                self.assertTrue(res is None)

        # test params exception
        with mock.patch("builtins.open", mock.mock_open(read_data="path.avm")):
            with mock.patch("neo.Prompt.Commands.LoadSmartContract.binascii", return_value=TypeError):
                res = LoadContract("path.avm", False, False, False, "070710", "01")

        self.assertTrue(res)

        # test params exception
        with mock.patch("builtins.open", mock.mock_open(read_data="path.avm")):
            with mock.patch("builtins.bytearray", return_value=TypeError):
                res = LoadContract("path.avm", False, False, False, "070710", "01")

        self.assertTrue(res)

        # test good contract
        with mock.patch("builtins.open", mock.mock_open(read_data="path.avm")):
            res = LoadContract("path.avm", True, True, True, "070710", "01")

        self.assertTrue(res)

        # test a contract with no params
        with mock.patch("builtins.open", mock.mock_open(read_data="path.avm")):
            res = LoadContract("path.avm", False, False, False, "", "01")

        self.assertTrue(res)

    def test_gatherloadedcontractparams(self):
        # test too few args
        with self.assertRaises(Exception) as e:
            args = []
            script = "script"

            GatherLoadedContractParams(args, script)

        self.assertTrue(
            "please specify contract properties like {needs_storage} {needs_dynamic_invoke} {is_payable} {params} {return_type}" in str(e.exception))

        # test for void (ff) type in params
        with self.assertRaises(ValueError) as e:
            args = ["False", "False", "False", "07ff10", "01"]
            script = b"script"

            GatherLoadedContractParams(args, script)

        self.assertTrue("Void is not a valid input parameter type" in str(e.exception))

        # test good params with needs_dynamic_invoke
        with mock.patch("neo.Prompt.Commands.LoadSmartContract.generate_deploy_script", return_value=True):
            args = ["False", "True", "False", "070710", "01"]
            script = "script"

            res = GatherLoadedContractParams(args, script)

        self.assertTrue(res)

        # test no required params
        with mock.patch("neo.Prompt.Commands.LoadSmartContract.generate_deploy_script", return_value=True):
            args = ["False", "False", "False", "", "01"]
            script = "script"

            res = GatherLoadedContractParams(args, script)

        self.assertTrue(res)
