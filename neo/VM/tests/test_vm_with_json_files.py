from neo.Utils.VMJSONTestCase import VMJSONTestCase
import glob
import io
import os
import json
from neo.VM.tests.JsonTester import execute_test


class VMTest(VMJSONTestCase):
    def test_files(self):
        """
        This downloads the *.JSON test files from the NEO-VM repo and runs all tests
        """
        for filename in glob.glob(os.path.dirname(self.SOURCE_FILENAME) + "/**/*.json", recursive=True):
            with io.open(filename, 'r', encoding='utf-8-sig') as f:  # uses dirty UTF-8 BOM header *sigh*
                data = json.load(f)
                execute_test(data)
