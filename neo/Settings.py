"""
The settings are dynamically configurable, for instance to set them depending on CLI arguments.
By default these are the testnet settings, but you can reconfigure them by calling the `setup(..)`
method.
"""
import json
import os
import sys
import logging
from json.decoder import JSONDecodeError


class SettingsHolder:
    """
    This class holds all the settings. Needs to be setup with one of the
    `setup` methods before using it.
    """
    MAGIC = None
    ADDRESS_VERSION = None
    STANDBY_VALIDATORS = None
    SEED_LIST = None

    ENROLLMENT_TX_FEE = None
    ISSUE_TX_FEE = None
    PUBLISH_TX_FEE = None
    REGISTER_TX_FEE = None

    LEVELDB_PATH = None
    NODE_PORT = None
    WS_PORT = None
    URI_PREFIX = None
    VERSION_NAME = None

    token_style = None
    config_file = None

    prefs_file_name = 'preferences.json'

    # Helpers
    @property
    def is_mainnet(self):
        """ Returns True if settings point to MainNet """
        return self.NODE_PORT == 10333 and self.MAGIC == 7630401

    @property
    def is_testnet(self):
        """ Returns True if settings point to TestNet """
        return self.NODE_PORT == 20333 and self.MAGIC == 1953787457

    @property
    def net_name(self):
        if self.MAGIC is None:
            return 'None'
        if self.is_mainnet:
            return 'MainNet'
        if self.is_testnet:
            return 'TestNet'
        return 'PrivateNet'

    def __init__(self):
        logging.basicConfig(level=logging.ERROR, format='%(levelname)s - %(name)s(L:%(lineno)s) - %(message)s')
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

    # Setup methods
    def setup(self, config_file):
        """ Load settings from a JSON config file """
        with open(config_file) as data_file:
            data = json.load(data_file)

        config = data['ProtocolConfiguration']
        self.MAGIC = config['Magic']
        self.ADDRESS_VERSION = config['AddressVersion']
        self.STANDBY_VALIDATORS = config['StandbyValidators']
        self.SEED_LIST = config['SeedList']

        fees = config['SystemFee']
        self.ENROLLMENT_TX_FEE = fees['EnrollmentTransaction']
        self.ISSUE_TX_FEE = fees['IssueTransaction']
        self.PUBLISH_TX_FEE = fees['PublishTransaction']
        self.REGISTER_TX_FEE = fees['RegisterTransaction']

        config = data['ApplicationConfiguration']
        self.LEVELDB_PATH = config['DataDirectoryPath']
        self.NODE_PORT = int(config['NodePort'])
        self.WS_PORT = config['WsPort']
        self.URI_PREFIX = config['UriPrefix']
        self.VERSION_NAME = config['VersionName']

        self.config_file = config_file

        prefs = self._load_preferences()
        if self._validate_or_restore_theme_data(prefs):
            self.token_style = prefs['themes'][prefs['theme']]

    def setup_mainnet(self):
        """ Load settings from the mainnet JSON config file """
        self.setup('protocol.mainnet.json')

    def setup_testnet(self):
        """ Load settings from the testnet JSON config file """
        self.setup('protocol.testnet.json')

    def restore_theme_preferences(self):
        data = self._load_preferences()
        data["theme"] = "dark"
        data["themes"] = {
            "dark": {
                "Command": "#ff0066",
                "Default": "#00ee00",
                "Neo": "#0000ee",
                "Number": "#ffffff"
            },
            "light": {
                "Command": "#ff0066",
                "Default": "#008800",
                "Neo": "#0000ee",
                "Number": "#000000"
            }
        }
        with open(self.prefs_file_name, "w") as data_file:
            data_file.write(json.dumps(data, indent=4, sort_keys=True))

    def set_theme(self, theme_name):
        if not os.path.isfile(self.prefs_file_name):
            self.restore_theme_preferences()

        data = self._load_preferences()
        data["theme"] = theme_name
        with open(self.prefs_file_name, "w") as data_file:
            data_file.write(json.dumps(data, indent=4, sort_keys=True))

        self.token_style = data['themes'][theme_name]

    def _load_preferences(self):
        with open(self.prefs_file_name) as data_file:
            try:
                prefs = json.load(data_file)
            except JSONDecodeError as e:
                self.logger.info("JSONDecodeError: {} in {}".format(e.msg, self.prefs_file_name))
                sys.exit(-1)
        return prefs

    def _validate_or_restore_theme_data(self, data):
        if "theme" not in data.keys() or "themes" not in data.keys():
            self.logger.info(
                "Theme data not found in {}. Restoring default theme preferences".format(self.prefs_file_name))
            self.restore_theme_preferences()
            sys.exit(-1)
        else:
            return True


# Settings instance used by external modules
settings = SettingsHolder()

# Load testnet settings as default
settings.setup_testnet()
