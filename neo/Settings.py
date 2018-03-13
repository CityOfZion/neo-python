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
import pip

from json.decoder import JSONDecodeError
import logzero

from neo import __version__
from neocore.Cryptography import Helper

from neorpc.Client import RPCClient
from neorpc.Settings import settings as rpc_settings


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


class PrivnetConnectionError(Exception):
    pass


class DependencyError(Exception):
    pass


def check_depdendencies():
    # Get installed packages
    installed_packages = pip.get_installed_distributions()
    installed_packages_list = sorted(["%s==%s" % (i.key, i.version) for i in installed_packages])

    # Now check if each package specified in requirements.txt is actually installed
    deps_filename = os.path.join(DIR_PROJECT_ROOT, "requirements.txt")
    with open(deps_filename, "r") as f:
        for dep in f.read().split():
            if not dep.lower() in installed_packages_list:
                raise DependencyError("Required dependency %s is not installed. Please run 'pip install -e .'." % dep)


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

    # Emit Notify events when smart contract execution failed. Use for debugging purposes only.
    emit_notify_events_on_sc_execution_error = False

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

    def setup_privnet(self, host=None):
        """
        Load settings from the privnet JSON config file

        Args:
            host (string, optional): if supplied, uses this IP or domain as neo nodes. The host must
                                     use these standard ports: P2P 20333, RPC 30333.
        """
        self.setup(FILENAME_SETTINGS_PRIVNET)
        if isinstance(host, str):
            if ":" in host:
                raise Exception("No protocol prefix or port allowed in host, use just the IP or domain.")
            print("Using custom privatenet host:", host)
            self.SEED_LIST = ["%s:20333" % host]
            self.RPC_LIST = ["http://%s:30333" % host]
            print("- P2P:", ", ".join(self.SEED_LIST))
            print("- RPC:", ", ".join(self.RPC_LIST))
        self.check_privatenet()

    def setup_coznet(self):
        """ Load settings from the coznet JSON config file """
        self.setup(FILENAME_SETTINGS_COZNET)

    def set_log_smart_contract_events(self, is_enabled=True):
        self.log_smart_contract_events = is_enabled

    def set_emit_notify_events_on_sc_execution_error(self, is_enabled=False):
        self.emit_notify_events_on_sc_execution_error = is_enabled

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

    def check_privatenet(self):
        """
        Check if privatenet is running, and if container is same as the current Chains/privnet database.

        Raises:
            PrivnetConnectionError: if the private net couldn't be reached or the nonce does not match
        """
        rpc_settings.setup(self.RPC_LIST)
        client = RPCClient()
        version = client.get_version()
        if not version:
            raise PrivnetConnectionError("Error: private network container doesn't seem to be running, or RPC is not enabled.")

        print("Privatenet useragent '%s', nonce: %s" % (version["useragent"], version["nonce"]))

        # Now check if nonce is the same as in the chain path
        nonce_container = str(version["nonce"])
        neopy_chain_meta_filename = os.path.join(self.LEVELDB_PATH, ".privnet-nonce")
        if os.path.isfile(neopy_chain_meta_filename):
            nonce_chain = open(neopy_chain_meta_filename, "r").read()
            if nonce_chain != nonce_container:
                raise PrivnetConnectionError(
                    "Chain database in Chains/privnet is for a different private network than the current container. "
                    "Consider deleting the Chain directory with 'rm -rf Chains/privnet*'."
                )
        else:
            with open(neopy_chain_meta_filename, "w") as f:
                f.write(nonce_container)


# Settings instance used by external modules
settings = SettingsHolder()

# Load testnet settings as default
settings.setup_testnet()

# By default, set loglevel to INFO. DEBUG just print a lot of internal debug statements
settings.set_loglevel(logging.INFO)

# Check if currently installed dependencies match the requirements
# Can be bypassed with `SKIP_DEPS_CHECK=1 python prompt.py`
if not os.getenv("SKIP_DEPS_CHECK"):
    check_depdendencies()
