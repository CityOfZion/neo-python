from unittest import TestCase
from neo.Prompt.Commands.LoadSmartContract import LoadContract, GatherLoadedContractParams
import mock


class LoadSmartContractTestCase(TestCase):

    def test_loadcontract(self):

        # test too few args
        args = []

        res = LoadContract(args)

        self.assertFalse(res)

        # test for void (ff) type in params
        with self.assertRaises(Exception) as e:
            args = ["path", "07ff10", "01", "False", "False", "False"]

            LoadContract(args)

        self.assertTrue("Void is an unsupported input type" in str(e.exception))

        # test for .py in path
        args = ["path.py", "070710", "01", "False", "False", "False"]

        res = LoadContract(args)

        self.assertFalse(res)

        # test good contract
        with mock.patch("builtins.open", mock.mock_open(read_data="path.avm")):

            args = ["path.avm", "070710", "01", "True", "True", "True"]

            res = LoadContract(args)

        self.assertTrue(res)

        # test bad contract
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
        with self.assertRaises(Exception) as e:
            args = ["07ff10", "01", "False", "False", "False"]
            script = b"script"

            GatherLoadedContractParams(args, script)

        self.assertTrue("Void is an unsupported input type" in str(e.exception))

        # test good params with needs_dynamic_invoke
        with mock.patch("neo.Prompt.Commands.LoadSmartContract.generate_deploy_script", return_value=True):
            args = ["070710", "01", "False", "True", "False"]
            script = "script"

            res = GatherLoadedContractParams(args, script)

        self.assertTrue(res)
