"""
These are the core network and system settings. For user-preferences, take a
look at `UserPreferences.py`.

The settings are dynamically configurable, for instance to set them depending
on CLI arguments. By default these are the testnet settings, but you can
reconfigure them by calling the `setup(..)` methods.
"""
import json
import logging
import os
import sys
import pip
from neocore.Cryptography import Helper
from neocore.Fixed8 import Fixed8
from neorpc.Client import RPCClient, NEORPCException
from neorpc.Settings import settings as rpc_settings
from neo import __version__
from logging.handlers import RotatingFileHandler
from logzero import LogFormatter
from neo.logging import log_manager

logger = log_manager.getLogger()

dir_current = os.path.dirname(os.path.abspath(__file__))

# ROOT_INSTALL_PATH is the root path of neo-python, whether installed as package or from git.
ROOT_INSTALL_PATH = os.path.abspath(os.path.join(dir_current, ".."))

# This detects if we are running from an 'editable' version (like ``python neo/bin/prompt.py``)
# or from a packaged install version from pip
IS_PACKAGE_INSTALL = 'site-packages/neo' in dir_current

# The filenames for various files. Might be improved by using system
# user directories: https://github.com/ActiveState/appdirs
FILENAME_PREFERENCES = os.path.join(ROOT_INSTALL_PATH, 'neo/data/preferences.json')

# The protocol json files are always in the project root
FILENAME_SETTINGS_MAINNET = os.path.join(ROOT_INSTALL_PATH, 'neo/data/protocol.mainnet.json')
FILENAME_SETTINGS_TESTNET = os.path.join(ROOT_INSTALL_PATH, 'neo/data/protocol.testnet.json')
FILENAME_SETTINGS_PRIVNET = os.path.join(ROOT_INSTALL_PATH, 'neo/data/protocol.privnet.json')
FILENAME_SETTINGS_COZNET = os.path.join(ROOT_INSTALL_PATH, 'neo/data/protocol.coz.json')
FILENAME_SETTINGS_UNITTEST_NET = os.path.join(ROOT_INSTALL_PATH, 'neo/data/protocol.unittest-net.json')


class PrivnetConnectionError(Exception):
    pass


class SystemCheckError(Exception):
    pass


def check_depdendencies():
    """
    Makes sure that all required dependencies are installed in the exact version
    (as specified in requirements.txt)
    """
    # Get installed packages
    installed_packages = pip.get_installed_distributions(local_only=False)
    installed_packages_list = sorted(["%s==%s" % (i.key, i.version) for i in installed_packages])

    # Now check if each package specified in requirements.txt is actually installed
    deps_filename = os.path.join(ROOT_INSTALL_PATH, "requirements.txt")
    with open(deps_filename, "r") as f:
        for dep in f.read().split():
            if not dep.lower() in installed_packages_list:
                raise SystemCheckError("Required dependency %s is not installed. Please run 'pip install -e .'" % dep)


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

    MAX_FREE_TX_SIZE = 1024
    FEE_PER_EXTRA_BYTE = 0.00001

    LOW_PRIORITY_THRESHOLD = Fixed8.FromDecimal(0.001)

    DATA_DIR_PATH = None
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
    DEBUG_STORAGE_PATH = 'Chains/debugstorage'

    ACCEPT_INCOMING_PEERS = False
    CONNECTED_PEER_MAX = 20

    SERVICE_ENABLED = True

    COMPILER_NEP_8 = True

    VERSION_NAME = "/NEO-PYTHON:%s/" % __version__

    RPC_SERVER = None
    REST_SERVER = None
    DEFAULT_RPC_SERVER = 'neo.api.JSONRPC.JsonRpcApi.JsonRpcApi'
    DEFAULT_REST_SERVER = 'neo.api.REST.RestApi.RestApi'

    # Logging settings
    log_level = None
    log_smart_contract_events = False
    log_vm_instructions = False

    # Emit Notify events when smart contract execution failed. Use for debugging purposes only.
    emit_notify_events_on_sc_execution_error = False

    rotating_filehandler = None

    @property
    def chain_leveldb_path(self):
        self.check_chain_dir_exists(warn_migration=True)
        return os.path.abspath(os.path.join(self.DATA_DIR_PATH, self.LEVELDB_PATH))

    @property
    def notification_leveldb_path(self):
        self.check_chain_dir_exists()
        return os.path.abspath(os.path.join(self.DATA_DIR_PATH, self.NOTIFICATION_DB_PATH))

    @property
    def debug_storage_leveldb_path(self):
        self.check_chain_dir_exists()
        return os.path.abspath(os.path.join(self.DATA_DIR_PATH, self.DEBUG_STORAGE_PATH))

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
        """ Setup settings from a JSON config file """

        def get_config_and_warn(key, default, abort=False):
            value = config.get(key, None)
            if not value:
                print(f"Cannot find {key} in settings, using default value: {default}")
                value = default
                if abort:
                    sys.exit(-1)
            return value

        if not self.DATA_DIR_PATH:
            # Setup default data dir
            self.set_data_dir(None)

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
        self.LEVELDB_PATH = config['DataDirectoryPath']
        self.RPC_PORT = int(config['RPCPort'])
        self.NODE_PORT = int(config['NodePort'])
        self.WS_PORT = config['WsPort']
        self.URI_PREFIX = config['UriPrefix']
        self.ACCEPT_INCOMING_PEERS = config.get('AcceptIncomingPeers', False)

        self.BOOTSTRAP_NAME = get_config_and_warn('BootstrapName', "mainnet")
        self.BOOTSTRAP_LOCATIONS = get_config_and_warn('BootstrapFiles', "abort", abort=True)
        Helper.ADDRESS_VERSION = self.ADDRESS_VERSION

        self.USE_DEBUG_STORAGE = config.get('DebugStorage', False)
        self.DEBUG_STORAGE_PATH = config.get('DebugStoragePath', 'Chains/debugstorage')
        self.NOTIFICATION_DB_PATH = config.get('NotificationDataPath', 'Chains/notification_data')
        self.SERVICE_ENABLED = config.get('ServiceEnabled', self.ACCEPT_INCOMING_PEERS)
        self.COMPILER_NEP_8 = config.get('CompilerNep8', False)
        self.REST_SERVER = config.get('RestServer', self.DEFAULT_REST_SERVER)
        self.RPC_SERVER = config.get('RPCServer', self.DEFAULT_RPC_SERVER)

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

    def setup_unittest_net(self, host=None):
        """ Load settings from privnet JSON config file. """
        self.setup(FILENAME_SETTINGS_UNITTEST_NET)

    def setup_coznet(self):
        """ Load settings from the coznet JSON config file """
        self.setup(FILENAME_SETTINGS_COZNET)

    def set_data_dir(self, path):
        if not path:
            path_user_home = os.path.expanduser('~')
            self.DATA_DIR_PATH = os.path.join(path_user_home, ".neopython")  # Works for both Windows and *nix
        elif path == '.':
            self.DATA_DIR_PATH = os.getcwd()
        else:
            self.DATA_DIR_PATH = path

        if not os.path.exists(self.DATA_DIR_PATH):
            os.makedirs(self.DATA_DIR_PATH)

    def set_max_peers(self, num_peers):
        maxpeers = int(num_peers)
        if maxpeers > 0:
            self.CONNECTED_PEER_MAX = maxpeers
        else:
            raise ValueError

    def set_log_smart_contract_events(self, is_enabled=True):
        self.log_smart_contract_events = is_enabled

    def set_log_vm_instruction(self, is_enabled=True):
        self.log_vm_instructions = is_enabled

    def set_emit_notify_events_on_sc_execution_error(self, is_enabled=False):
        self.emit_notify_events_on_sc_execution_error = is_enabled

    def set_logfile(self, filename, max_bytes=0, backup_count=0):
        """
        Setup logging to a (rotating) logfile.

        Args:
            filename (str): Logfile. If filename is None, disable file logging
            max_bytes (int): Maximum number of bytes per logfile. If used together with backup_count,
                             logfile will be rotated when it reaches this amount of bytes.
            backup_count (int): Number of rotated logfiles to keep
        """
        _logger = logging.getLogger("neo-python")

        if not filename and not self.rotating_filehandler:
            _logger.removeHandler(self.rotating_filehandler)
        else:
            self.rotating_filehandler = RotatingFileHandler(filename, mode='a', maxBytes=max_bytes, backupCount=backup_count, encoding=None)
            self.rotating_filehandler.setLevel(logging.DEBUG)
            self.rotating_filehandler.setFormatter(LogFormatter(color=False))
            _logger.addHandler(self.rotating_filehandler)

    def set_loglevel(self, level):
        """
        Set the minimum loglevel for all components

        Args:
            level (int): eg. logging.DEBUG or logging.ERROR. See also https://docs.python.org/2/library/logging.html#logging-levels
        """
        self.log_level = level
        log_manager.config_stdio(default_level=level)

    def check_chain_dir_exists(self, warn_migration=False):
        """
        Checks to make sure there is a directory called ``Chains`` at the root of DATA_DIR_PATH
        and creates it if it doesn't exist yet
        """
        chain_path = os.path.join(self.DATA_DIR_PATH, 'Chains')

        if not os.path.exists(chain_path):
            try:
                os.makedirs(chain_path)
                logger.info("Created 'Chains' directory at %s " % chain_path)
            except Exception as e:
                logger.error("Could not create 'Chains' directory at %s %s" % (chain_path, e))

        warn_migration = False
        # Add a warning for migration purposes if we created a chain dir
        if warn_migration and ROOT_INSTALL_PATH != self.DATA_DIR_PATH:
            if os.path.exists(os.path.join(ROOT_INSTALL_PATH, 'Chains')):
                logger.warning("[MIGRATION] You are now using the blockchain data at %s, but it appears you have existing data at %s/Chains" % (
                    chain_path, ROOT_INSTALL_PATH))
                logger.warning(
                    "[MIGRATION] If you would like to use your existing data, please move any data at %s/Chains to %s " % (ROOT_INSTALL_PATH, chain_path))
                logger.warning("[MIGRATION] Or you can continue using your existing data by starting your script with the `--datadir=.` flag")

    def check_privatenet(self):
        """
        Check if privatenet is running, and if container is same as the current Chains/privnet database.

        Raises:
            PrivnetConnectionError: if the private net couldn't be reached or the nonce does not match
        """
        rpc_settings.setup(self.RPC_LIST)
        client = RPCClient()

        try:
            version = client.get_version()
        except NEORPCException:
            raise PrivnetConnectionError("Error: private network container doesn't seem to be running, or RPC is not enabled.")

        print("Privatenet useragent '%s', nonce: %s" % (version["useragent"], version["nonce"]))

        # Now check if nonce is the same as in the chain path
        nonce_container = str(version["nonce"])
        neopy_chain_meta_filename = os.path.join(self.chain_leveldb_path, ".privnet-nonce")
        if os.path.isfile(neopy_chain_meta_filename):
            nonce_chain = open(neopy_chain_meta_filename, "r").read()
            if nonce_chain != nonce_container:
                raise PrivnetConnectionError(
                    "Chain database in Chains/privnet is for a different private network than the current container. "
                    "Consider deleting the Chain directory with 'rm -rf %s*'." % self.chain_leveldb_path
                )
        else:
            # When the Chains/privnet folder is removed, we need to create the directory
            if not os.path.isdir(self.chain_leveldb_path):
                os.mkdir(self.chain_leveldb_path)

            # Write the nonce to the meta file
            with open(neopy_chain_meta_filename, "w") as f:
                f.write(nonce_container)


# Settings instance used by external modules
settings = SettingsHolder()

# Load testnet settings as default. This is useful to provide default data/db directories
# to any code using "from neo.Settings import settings"
settings.setup_testnet()

# By default, set loglevel to INFO. DEBUG just print a lot of internal debug statements
settings.set_loglevel(logging.INFO)

# System check: Are dependencies must be installed in the correct version
# Can be bypassed with `SKIP_DEPS_CHECK=1 python prompt.py`
# this causes so many headaches when developing between boa and neo and core... :(
# if not os.getenv("SKIP_DEPS_CHECK") and not IS_PACKAGE_INSTALL:
#     check_depdendencies()

# System check: Python 3.6+
if not os.getenv("SKIP_PY_CHECK"):
    if sys.version_info < (3, 6):
        raise SystemCheckError("Needs Python 3.6+. Currently used: %s" % sys.version)
