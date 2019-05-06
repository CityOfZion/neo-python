import tarfile
import requests
import shutil
import os
from neo.Utils.NeoTestCase import NeoTestCase
from neo.Settings import settings
from neo.logging import log_manager

logger = log_manager.getLogger()


class VMJSONTestCase(NeoTestCase):
    NEO_VM_REPO_URL = "https://github.com/neo-project/neo-vm/tarball/cd5c3d0460bd1d4acce34be91c38a2ccfca8050f"
    SOURCE_FILENAME = os.path.join(settings.DATA_DIR_PATH, 'vm-tests/neo-vm.tar.gz')

    @classmethod
    def setUpClass(cls):

        logger.info("Downloading JSON VM fixtures from the NEO-VM project")

        response = requests.get(cls.NEO_VM_REPO_URL, stream=True)
        response.raise_for_status()

        os.makedirs(os.path.dirname(cls.SOURCE_FILENAME), exist_ok=True)
        with open(cls.SOURCE_FILENAME, 'wb+') as handle:
            for block in response.iter_content(1024):
                handle.write(block)

        try:
            tar = tarfile.open(cls.SOURCE_FILENAME)
            to_extract = []
            for n in tar.getmembers():
                if "json" in n.name:
                    to_extract.append(n)
            tar.extractall(path=os.path.dirname(cls.SOURCE_FILENAME), members=to_extract)
            tar.close()
        except Exception as e:
            raise Exception(f"Could not extract tar file - {cls.SOURCE_FILENAME} {e}")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(os.path.dirname(cls.SOURCE_FILENAME))
