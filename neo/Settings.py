"""
The settings are dynamically configurable, for instance to set them depending on CLI arguments.
By default these are the testnet settings, but you can reconfigure them by calling the `setup(..)`
method.
"""
import json


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

    # Helpers
    @property
    def is_mainnet(self):
        """ Returns True if settings point to MainNet """
        return self.NODE_PORT == 10333

    @property
    def is_testnet(self):
        """ Returns True if settings point to TestNet """
        return self.NODE_PORT == 20333

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

        self.token_style = config['themes'][config['theme']]
        self.config_file = config_file

    def setup_mainnet(self):
        """ Load settings from the mainnet JSON config file """
        self.setup('protocol.mainnet.json')

    def setup_testnet(self):
        """ Load settings from the testnet JSON config file """
        self.setup('protocol.testnet.json')

    def set_theme(self, theme_name):
        with open(self.config_file) as data_file:
            data = json.load(data_file)

        data["ApplicationConfiguration"]["theme"] = theme_name
        with open(self.config_file, "w") as data_file:
            data_file.write(json.dumps(data, indent=4, sort_keys=True))

        self.token_style = data['ApplicationConfiguration']['themes'][theme_name]


# Settings instance used by external modules
settings = SettingsHolder()

# Load testnet settings as default
settings.setup_testnet()
