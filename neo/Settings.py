
import json


with open('protocol.testnet.json') as data_file:

    data = json.load(data_file)

config = data['ProtocolConfiguration']


MAGIC = config['Magic']
ADDRESS_VERSION = config['AddressVersion']
STANDBY_VALIDATORS = config['StandbyValidators']
SEED_LIST = config['SeedList']

fees = config['SystemFee']

ENROLLMENT_TX_FEE = fees['EnrollmentTransaction']
ISSUE_TX_FEE = fees['IssueTransaction']
PUBLISH_TX_FEE = fees['PublishTransaction']
REGISTER_TX_FEE = fees['RegisterTransaction']



config = data['ApplicationConfiguration']

LEVELDB_PATH= config['DataDirectoryPath']
NODE_PORT = int(config['NodePort'])
WS_PORT = config['WsPort']
URI_PREFIX = config['UriPrefix']
VERSION_NAME = config['VersionName']
