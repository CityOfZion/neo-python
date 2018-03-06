"""
These are the core network and system settings. For user-preferences, take a
look at `UserPreferences.py`.

The settings are dynamically configurable, for instance to set them depending
on CLI arguments. By default these are the testnet settings, but you can
reconfigure them by calling the `setup(..)` methods.
"""
import json
import os
import logging
from json.decoder import JSONDecodeError

from neo import __version__
from neocore.Cryptography import Helper

import logzero

# Create am absolute references to the project root folder. Used for
# specifying the various filenames.
dir_current = os.path.dirname(os.path.abspath(__file__))
DIR_PROJECT_ROOT = os.path.abspath(os.path.join(dir_current, ".."))

# The filenames for various files. Might be improved by using system
# user directories: https://github.com/ActiveState/appdirs
FILENAME_PREFERENCES = os.path.join(DIR_PROJECT_ROOT, 'preferences.json')

# The protocol json files are always in the project root
FILENAME_SETTINGS_MAINNET = os.path.join(DIR_PROJECT_ROOT, 'protocol.mainnet.json')
FILENAME_SETTINGS_TESTNET = os.path.join(DIR_PROJECT_ROOT, 'protocol.testnet.json')
FILENAME_SETTINGS_PRIVNET = os.path.join(DIR_PROJECT_ROOT, 'protocol.privnet.json')
FILENAME_SETTINGS_COZNET = os.path.join(DIR_PROJECT_ROOT, 'protocol.coz.json')


class SettingsHolder:
    """
    This class holds all the settings. Needs to be setup with one of the
    `setup` methods before using it.
    """
    MAGIC = None
    ADDRESS_VERSION = None
    STANDBY_VALIDATORS = None
    SEED_LIST = None
    RPC_LIST = None

    ENROLLMENT_TX_FEE = None
    ISSUE_TX_FEE = None
    PUBLISH_TX_FEE = None
    REGISTER_TX_FEE = None

    LEVELDB_PATH = None
    NOTIFICATION_DB_PATH = None

    RPC_PORT = None
    NODE_PORT = None
    WS_PORT = None
    URI_PREFIX = None
    BOOTSTRAP_FILE = None
    NOTIF_BOOTSTRAP_FILE = None

    ALL_FEES = None
    USE_DEBUG_STORAGE = False
    DEBUG_STORAGE_PATH = './Chains/debugstorage'

    VERSION_NAME = "/NEO-PYTHON:%s/" % __version__

    # Logging settings
    log_smart_contract_events = False

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
    def is_coznet(self):
        """ Returns True if settings point to CoZnet """
        return self.NODE_PORT == 20333 and self.MAGIC == 1010102

    @property
    def net_name(self):
        if self.MAGIC is None:
            return 'None'
        if self.is_mainnet:
            return 'MainNet'
        if self.is_testnet:
            return 'TestNet'
        if self.is_coznet:
            return 'CozNet'
        return 'PrivateNet'

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
        self.RPC_LIST = config['RPCList']

        fees = config['SystemFee']
        self.ALL_FEES = fees
        self.ENROLLMENT_TX_FEE = fees['EnrollmentTransaction']
        self.ISSUE_TX_FEE = fees['IssueTransaction']
        self.PUBLISH_TX_FEE = fees['PublishTransaction']
        self.REGISTER_TX_FEE = fees['RegisterTransaction']

        config = data['ApplicationConfiguration']
        self.LEVELDB_PATH = os.path.join(DIR_PROJECT_ROOT, config['DataDirectoryPath'])
        self.RPC_PORT = int(config['RPCPort'])
        self.NODE_PORT = int(config['NodePort'])
        self.WS_PORT = config['WsPort']
        self.URI_PREFIX = config['UriPrefix']

        self.BOOTSTRAP_FILE = config['BootstrapFile']
        self.NOTIF_BOOTSTRAP_FILE = config['NotificationBootstrapFile']

        Helper.ADDRESS_VERSION = self.ADDRESS_VERSION

        if 'DebugStorage' in config:
            self.USE_DEBUG_STORAGE = config['DebugStorage']

        if 'DebugStoragePath' in config:
            self.DEBUG_STORAGE_PATH = config['DebugStoragePath']

        if 'NotificationDataPath' in config:
            self.NOTIFICATION_DB_PATH = os.path.join(DIR_PROJECT_ROOT, config['NotificationDataPath'])

    def setup_mainnet(self):
        """ Load settings from the mainnet JSON config file """
        self.setup(FILENAME_SETTINGS_MAINNET)

    def setup_testnet(self):
        """ Load settings from the testnet JSON config file """
        self.setup(FILENAME_SETTINGS_TESTNET)

    def setup_privnet(self):
        """ Load settings from the privnet JSON config file """
        self.setup(FILENAME_SETTINGS_PRIVNET)

    def setup_coznet(self):
        """ Load settings from the coznet JSON config file """
        self.setup(FILENAME_SETTINGS_COZNET)

    def set_log_smart_contract_events(self, is_enabled=True):
        self.log_smart_contract_events = is_enabled

    def set_logfile(self, fn, max_bytes=0, backup_count=0):
        """
        Setup logging to a (rotating) logfile.

        Args:
            fn (str): Logfile. If fn is None, disable file logging
            max_bytes (int): Maximum number of bytes per logfile. If used together with backup_count,
                             logfile will be rotated when it reaches this amount of bytes.
            backup_count (int): Number of rotated logfiles to keep
        """
        logzero.logfile(fn, maxBytes=max_bytes, backupCount=backup_count)

    def set_loglevel(self, level):
        """
        Set the minimum loglevel for the default logger

        Args:
            level (int): eg. logging.DEBUG or logging.ERROR. See also https://docs.python.org/2/library/logging.html#logging-levels
        """
        logzero.loglevel(level)


# Settings instance used by external modules
settings = SettingsHolder()

# Load testnet settings as default
settings.setup_testnet()

# By default, set loglevel to INFO. DEBUG just print a lot of internal debug statements
settings.set_loglevel(logging.INFO)
