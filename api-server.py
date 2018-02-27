#!/usr/bin/env python3
"""
This api server runs both a json-rpc api and a notification rest api.
(neo.api.JSONRPC.JsonRpcApi and neo.api.REST.NotificationRestApi)

Example systemd service config: TODO
"""
import os
import argparse
import threading
from time import sleep

from logzero import logger
from twisted.internet import reactor, task

from neo import __version__
from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB
from neo.api.JSONRPC.JsonRpcApi import JsonRpcApi
from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB
from neo.api.REST.NotificationRestApi import NotificationRestApi

from neo.Network.NodeLeader import NodeLeader
from neo.Settings import settings, DIR_PROJECT_ROOT
from neo.UserPreferences import preferences

# Logfile settings & setup
LOGFILE_FN = os.path.join(DIR_PROJECT_ROOT, 'api-server.log')
LOGFILE_MAX_BYTES = 5e7  # 50 MB
LOGFILE_BACKUP_COUNT = 3  # 3 logfiles history
settings.set_logfile(LOGFILE_FN, LOGFILE_MAX_BYTES, LOGFILE_BACKUP_COUNT)


def write_pid_file():
    """ Write a pid file, to easily kill the service """
    f = open('/tmp/json-rpc-api-server.pid', 'w')
    f.write(str(os.getpid()))
    f.close()


def custom_background_code():
    """ Custom code run in a background thread.

    This function is run in a daemonized thread, which means it can be instantly killed at any
    moment, whenever the main thread quits. If you need more safety, don't use a  daemonized
    thread and handle exiting this thread in another way (eg. with signals and events).
    """
    while True:
        logger.info("[%s] Block %s / %s", settings.net_name, str(Blockchain.Default().Height), str(Blockchain.Default().HeaderHeight))
        sleep(15)


def main():
    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-m", "--mainnet", action="store_true", default=False,
                       help="Use MainNet instead of the default TestNet")
    group.add_argument("-p", "--privnet", action="store_true", default=False,
                       help="Use PrivNet instead of the default TestNet")
    group.add_argument("--coznet", action="store_true", default=False,
                       help="Use the CoZ network instead of the default TestNet")
    group.add_argument("-c", "--config", action="store", help="Use a specific config file")

    parser.add_argument("--port", type=int, help="port to use for the server", required=True)
    parser.add_argument('mode', choices=["jsonrpc", "notifiationapi"])

    args = parser.parse_args()

    # Setup depending on command line arguments. By default, the testnet settings are already loaded.
    if args.config:
        settings.setup(args.config)
    elif args.mainnet:
        settings.setup_mainnet()
    elif args.privnet:
        settings.setup_privnet()
    elif args.coznet:
        settings.setup_coznet()

    # Write a PID file to easily quit the service
    write_pid_file()

    # Instantiate the blockchain and subscribe to notifications
    blockchain = LevelDBBlockchain(settings.LEVELDB_PATH)
    Blockchain.RegisterBlockchain(blockchain)
    dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
    dbloop.start(.1)

    settings.set_log_smart_contract_events(False)

    ndb = NotificationDB.instance()
    ndb.start()

    # Start a thread with custom code
    d = threading.Thread(target=custom_background_code)
    d.setDaemon(True)  # daemonizing the thread will kill it when the main thread is quit
    d.start()

    # Run
    reactor.suggestThreadPoolSize(15)
    NodeLeader.Instance().Start()

    host = "0.0.0.0"
    port = args.port

    if args.mode == "jsonrpc":
        logger.info("Starting json-rpc api server on http://%s:%s" % (host, port))
        api_server = JsonRpcApi(port)

    elif args.mode == "notifiationapi":
        logger.info("Starting notification api server on http://%s:%s" % (host, port))
        api_server = NotificationRestApi()
        ndb = NotificationDB.instance()
        ndb.start()

    api_server.app.run(host, port)


if __name__ == "__main__":
    main()
