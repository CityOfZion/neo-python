from neo.Utils.NeoTestCase import NeoTestCase
from neo.Settings import SettingsHolder, ROOT_INSTALL_PATH
import os


class SettingsTestCase(NeoTestCase):
    def test_settings(self):
        _settings = SettingsHolder()

        # Validate initial state
        self.assertEqual(_settings.MAGIC, None)
        self.assertEqual(_settings.ADDRESS_VERSION, None)
        self.assertEqual(_settings.STANDBY_VALIDATORS, None)
        self.assertEqual(_settings.is_mainnet, False)
        self.assertEqual(_settings.is_testnet, False)

        # Validate correct mainnet state
        _settings.setup_mainnet()
        self.assertEqual(_settings.is_mainnet, True)
        self.assertEqual(_settings.is_testnet, False)
        self.assertEqual(_settings.net_name, 'MainNet')

        # Validate correct testnet state
        _settings.setup_testnet()
        self.assertEqual(_settings.is_mainnet, False)
        self.assertEqual(_settings.is_testnet, True)
        self.assertEqual(_settings.net_name, 'TestNet')

        _settings.MAGIC = 1234567
        self.assertEqual(_settings.net_name, 'PrivateNet')

        _settings.MAGIC = None
        self.assertEqual(_settings.net_name, 'None')

    def test_data_dir_settings(self):

        _settings = SettingsHolder()

        # Validate correct mainnet state
        _settings.setup_mainnet()

        _settings.set_data_dir('.')

        self.assertEqual(_settings.chain_leveldb_path, os.path.abspath(os.path.join(ROOT_INSTALL_PATH, _settings.LEVELDB_PATH)))
        self.assertEqual(_settings.notification_leveldb_path, os.path.abspath(os.path.join(ROOT_INSTALL_PATH, _settings.NOTIFICATION_DB_PATH)))
        self.assertEqual(_settings.debug_storage_leveldb_path, os.path.abspath(os.path.join(ROOT_INSTALL_PATH, _settings.DEBUG_STORAGE_PATH)))

        _settings.DATA_DIR_PATH = '/tmp/whatever'

        self.assertEqual(_settings.chain_leveldb_path, os.path.abspath(os.path.join('/tmp/whatever', _settings.LEVELDB_PATH)))
        self.assertEqual(_settings.notification_leveldb_path, os.path.abspath(os.path.join('/tmp/whatever', _settings.NOTIFICATION_DB_PATH)))
        self.assertEqual(_settings.debug_storage_leveldb_path, os.path.abspath(os.path.join('/tmp/whatever', _settings.DEBUG_STORAGE_PATH)))
