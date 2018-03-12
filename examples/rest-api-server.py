#!/usr/bin/env python3
"""
This example provides a REST API to query notifications from the blockchain, implementing `neo.api.RESTAPI.RestApi`
See it live here: http://notifications.neeeo.org/

See also api-server.py for a more complete API implementation
"""

import argparse
import os

from logzero import logger
from twisted.internet import reactor, task

from neo import __version__
from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB
from neo.api.REST.RestApi import RestApi
from neo.Network.NodeLeader import NodeLeader
from neo.Settings import settings, DIR_PROJECT_ROOT
from neo.UserPreferences import preferences

# Logfile settings & setup
LOGFILE_FN = os.path.join(DIR_PROJECT_ROOT, 'notifications.log')
LOGFILE_MAX_BYTES = 5e7  # 50 MB
LOGFILE_BACKUP_COUNT = 3  # 3 logfiles history
settings.set_logfile(LOGFILE_FN, LOGFILE_MAX_BYTES, LOGFILE_BACKUP_COUNT)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mainnet", action="store_true", default=False,
                        help="Use MainNet instead of the default TestNet")
    parser.add_argument("-p", "--privnet", action="store_true", default=False,
                        help="Use PrivNet instead of the default TestNet")
    parser.add_argument("-c", "--config", action="store", help="Use a specific config file")
    parser.add_argument('--version', action='version',
                        version='neo-python v{version}'.format(version=__version__))

    args = parser.parse_args()

    if args.config and (args.mainnet or args.privnet):
        print("Cannot use both --config and --mainnet/--privnet arguments, please use only one.")
        exit(1)
    if args.mainnet and args.privnet:
        print("Cannot use both --mainnet and --privnet arguments")
        exit(1)

    # Setup depending on command line arguments. By default, the testnet settings are already loaded.
    if args.config:
        settings.setup(args.config)
    elif args.mainnet:
        settings.setup_mainnet()
    elif args.privnet:
        settings.setup_privnet()

    # Instantiate the blockchain and subscribe to notifications
    blockchain = LevelDBBlockchain(settings.LEVELDB_PATH)
    Blockchain.RegisterBlockchain(blockchain)
    dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
    dbloop.start(.1)

    ndb = NotificationDB.instance()
    ndb.start()

    api_server = RestApi()

    # Run
    reactor.suggestThreadPoolSize(15)
    NodeLeader.Instance().Start()

    port = 8000
    logger.info("Starting rest-api server on port %s" % (port))
    api_server.app.run('0.0.0.0', port)


if __name__ == "__main__":
    main()
