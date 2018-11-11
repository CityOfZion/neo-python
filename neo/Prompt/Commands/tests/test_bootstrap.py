from unittest import TestCase
from neo.Prompt.Commands.Bootstrap import BootstrapBlockchainFile
import os
import shutil


class BootstrapTestCase(TestCase):
    bootstrap_unittest_file_locations = 'https://s3.us-east-2.amazonaws.com/cityofzion/bootstrap_unittest_latest'

    bootstrap_target_dir = './fixtures/bootstrap_test'
    bootstrap_target_dir_bad = 'does_not_exist'

    def setUp(self):
        pass

    def tearDown(self):
        try:
            shutil.rmtree(self.bootstrap_target_dir)
        except Exception as e:
            pass

    def test_1_bad_bootstrap_file(self):
        # this should exit 0
        print("***                                     ***")
        print("*** This test expects a `404 Not found` ***")
        print("***                                     ***")
        with self.assertRaises(SystemExit):
            BootstrapBlockchainFile(self.bootstrap_target_dir, self.bootstrap_unittest_file_locations, "badnet", require_confirm=False)

        # make sure no files are left around
        self.assertFalse(os.path.exists(self.bootstrap_target_dir))

    def test_2_good_bootstrap_file(self):
        with self.assertRaises(SystemExit):
            BootstrapBlockchainFile(self.bootstrap_target_dir, self.bootstrap_unittest_file_locations, "goodnet", require_confirm=False)

        self.assertTrue(os.path.exists(self.bootstrap_target_dir))

    def test_3_good_bootstrap_bad_path(self):
        with self.assertRaises(SystemExit):
            BootstrapBlockchainFile(self.bootstrap_target_dir_bad, self.bootstrap_unittest_file_locations, "goodnet", require_confirm=False)

        self.assertFalse(os.path.exists(self.bootstrap_target_dir))
