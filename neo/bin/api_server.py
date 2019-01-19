#!/usr/bin/env python3
"""
API server to run the JSON-RPC and REST API.

Uses servers specified in protocol.xxx.json files

Print the help and all possible arguments:

    ./api-server.py -h

Run using TestNet with JSON-RPC API at port 10332 and REST API at port 8080:

    ./api-server.py --testnet --port-rpc 10332 --port-rest 8080

See also:

* If you encounter any issues, please report them here: https://github.com/CityOfZion/neo-python/issues/273
* Server setup
  * Guide for Ubuntu server setup: https://gist.github.com/metachris/2be27cdff9503ebe7db1c27bfc60e435
  * Systemd service config: https://gist.github.com/metachris/03d1cc47df7cddfbc4009d5249bdfc6c
  * Ansible playbook to update nodes: https://gist.github.com/metachris/2be27cdff9503ebe7db1c27bfc60e435

Logging
-------

This api-server can log to stdout/stderr, logfile and syslog.
Check `api-server.py -h` for more details.

Twisted uses a quite custom logging setup. Here we simply setup the Twisted logger
to reuse our logzero logging setup. See also:

* http://twisted.readthedocs.io/en/twisted-17.9.0/core/howto/logger.html
* https://twistedmatrix.com/documents/17.9.0/api/twisted.logger.STDLibLogObserver.html
"""
import os
import sys
import argparse
import threading
from time import sleep
from logging.handlers import SysLogHandler

import logzero
from logzero import logger
from prompt_toolkit import prompt

# Twisted logging
from twisted.logger import STDLibLogObserver, globalLogPublisher

# Twisted and Klein methods and modules
from twisted.internet import reactor, task, endpoints, threads
from twisted.web.server import Site

# neo methods and modules
from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB
from neo.Wallets.utils import to_aes_key
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet

from neo.Network.NodeLeader import NodeLeader
from neo.Settings import settings
from neo.Utils.plugin import load_class_from_path
import neo.Settings

# Logfile default settings (only used if --logfile arg is used)
LOGFILE_MAX_BYTES = 5e7  # 50 MB
LOGFILE_BACKUP_COUNT = 3  # 3 logfiles history

# Set the PID file, possible to override with env var PID_FILE
PID_FILE = os.getenv("PID_FILE", "/tmp/neopython-api-server.pid")

continue_persisting = True
block_deferred = None


def write_pid_file():
    """ Write a pid file, to easily kill the service """
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def custom_background_code():
    """ Custom code run in a background thread.

    This function is run in a daemonized thread, which means it can be instantly killed at any
    moment, whenever the main thread quits. If you need more safety, don't use a  daemonized
    thread and handle exiting this thread in another way (eg. with signals and events).
    """
    while True:
        logger.info("[%s] Block %s / %s", settings.net_name, str(Blockchain.Default().Height + 1), str(Blockchain.Default().HeaderHeight + 1))
        sleep(15)


def on_persistblocks_error(err):
    logger.debug("On Persist blocks loop error! %s " % err)


def stop_block_persisting():
    global continue_persisting
    continue_persisting = False


def persist_done(value):
    """persist callback. Value is unused"""
    if continue_persisting:
        start_block_persisting()
    else:
        block_deferred.cancel()


def start_block_persisting():
    global block_deferred
    block_deferred = threads.deferToThread(Blockchain.Default().PersistBlocks)
    block_deferred.addCallback(persist_done)
    block_deferred.addErrback(on_persistblocks_error)


def main():
    parser = argparse.ArgumentParser()

    # Network options
    group_network_container = parser.add_argument_group(title="Network options")
    group_network = group_network_container.add_mutually_exclusive_group(required=True)
    group_network.add_argument("--mainnet", action="store_true", default=False, help="Use MainNet")
    group_network.add_argument("--testnet", action="store_true", default=False, help="Use TestNet")
    group_network.add_argument("--privnet", action="store_true", default=False, help="Use PrivNet")
    group_network.add_argument("--coznet", action="store_true", default=False, help="Use CozNet")
    group_network.add_argument("--config", action="store", help="Use a specific config file")

    # Ports for RPC and REST api
    group_modes = parser.add_argument_group(title="Mode(s)")
    group_modes.add_argument("--port-rpc", type=int, help="port to use for the json-rpc api (eg. 10332)")
    group_modes.add_argument("--port-rest", type=int, help="port to use for the rest api (eg. 80)")

    # Advanced logging setup
    group_logging = parser.add_argument_group(title="Logging options")
    group_logging.add_argument("--logfile", action="store", type=str, help="Logfile")
    group_logging.add_argument("--syslog", action="store_true", help="Log to syslog instead of to log file ('user' is the default facility)")
    group_logging.add_argument("--syslog-local", action="store", type=int, choices=range(0, 7), metavar="[0-7]",
                               help="Log to a local syslog facility instead of 'user'. Value must be between 0 and 7 (e.g. 0 for 'local0').")
    group_logging.add_argument("--disable-stderr", action="store_true", help="Disable stderr logger")

    # Where to store stuff
    parser.add_argument("--datadir", action="store",
                        help="Absolute path to use for database directories")
    # peers
    parser.add_argument("--maxpeers", action="store", default=5,
                        help="Max peers to use for P2P Joining")

    # If a wallet should be opened
    parser.add_argument("--wallet",
                        action="store",
                        help="Open wallet. Will allow you to use methods that require an open wallet")

    # host
    parser.add_argument("--host", action="store", type=str, help="Hostname ( for example 127.0.0.1)", default="0.0.0.0")

    # Now parse
    args = parser.parse_args()
    # print(args)

    if not args.port_rpc and not args.port_rest:
        print("Error: specify at least one of --port-rpc / --port-rest")
        parser.print_help()
        return

    if args.port_rpc == args.port_rest:
        print("Error: --port-rpc and --port-rest cannot be the same")
        parser.print_help()
        return

    if args.logfile and (args.syslog or args.syslog_local):
        print("Error: Cannot only use logfile or syslog at once")
        parser.print_help()
        return

    # Setting the datadir must come before setting the network, else the wrong path is checked at net setup.
    if args.datadir:
        settings.set_data_dir(args.datadir)

    # Network configuration depending on command line arguments. By default, the testnet settings are already loaded.
    if args.config:
        settings.setup(args.config)
    elif args.mainnet:
        settings.setup_mainnet()
    elif args.testnet:
        settings.setup_testnet()
    elif args.privnet:
        settings.setup_privnet()
    elif args.coznet:
        settings.setup_coznet()

    if args.maxpeers:
        try:
            settings.set_max_peers(args.maxpeers)
            print("Maxpeers set to ", args.maxpeers)
        except ValueError:
            print("Please supply a positive integer for maxpeers")
            return  

    if args.syslog or args.syslog_local is not None:
        # Setup the syslog facility
        if args.syslog_local is not None:
            print("Logging to syslog local%s facility" % args.syslog_local)
            syslog_facility = SysLogHandler.LOG_LOCAL0 + args.syslog_local
        else:
            print("Logging to syslog user facility")
            syslog_facility = SysLogHandler.LOG_USER

        # Setup logzero to only use the syslog handler
        logzero.syslog(facility=syslog_facility)
    else:
        # Setup file logging
        if args.logfile:
            logfile = os.path.abspath(args.logfile)
            if args.disable_stderr:
                print("Logging to logfile: %s" % logfile)
            else:
                print("Logging to stderr and logfile: %s" % logfile)
            logzero.logfile(logfile, maxBytes=LOGFILE_MAX_BYTES, backupCount=LOGFILE_BACKUP_COUNT, disableStderrLogger=args.disable_stderr)

        else:
            print("Logging to stdout and stderr")

    if args.wallet:
        if not os.path.exists(args.wallet):
            print("Wallet file not found")
            return

        passwd = os.environ.get('NEO_PYTHON_JSONRPC_WALLET_PASSWORD', None)
        if not passwd:
            passwd = prompt("[password]> ", is_password=True)

        password_key = to_aes_key(passwd)
        try:
            wallet = UserWallet.Open(args.wallet, password_key)

        except Exception as e:
            print(f"Could not open wallet {e}")
            return
    else:
        wallet = None

    # Disable logging smart contract events
    settings.set_log_smart_contract_events(False)

    # Write a PID file to easily quit the service
    write_pid_file()

    # Setup Twisted and Klein logging to use the logzero setup
    observer = STDLibLogObserver(name=logzero.LOGZERO_DEFAULT_LOGGER)
    globalLogPublisher.addObserver(observer)

    def loopingCallErrorHandler(error):
        logger.info("Error in loop: %s " % error)

    # Instantiate the blockchain and subscribe to notifications
    blockchain = LevelDBBlockchain(settings.chain_leveldb_path)
    Blockchain.RegisterBlockchain(blockchain)

    start_block_persisting()

    # If a wallet is open, make sure it processes blocks
    if wallet:
        walletdb_loop = task.LoopingCall(wallet.ProcessBlocks)
        wallet_loop_deferred = walletdb_loop.start(1)
        wallet_loop_deferred.addErrback(loopingCallErrorHandler)

    # Setup twisted reactor, NodeLeader and start the NotificationDB
    reactor.suggestThreadPoolSize(15)
    NodeLeader.Instance().Start()
    NotificationDB.instance().start()

    # Start a thread with custom code
    d = threading.Thread(target=custom_background_code)
    d.setDaemon(True)  # daemonizing the thread will kill it when the main thread is quit
    d.start()

    if args.port_rpc:
        logger.info("Starting json-rpc api server on http://%s:%s" % (args.host, args.port_rpc))
        try:
            rpc_class = load_class_from_path(settings.RPC_SERVER)
        except ValueError as err:
            logger.error(err)
            sys.exit()
        api_server_rpc = rpc_class(args.port_rpc, wallet=wallet)

        endpoint_rpc = "tcp:port={0}:interface={1}".format(args.port_rpc, args.host)
        endpoints.serverFromString(reactor, endpoint_rpc).listen(Site(api_server_rpc.app.resource()))

    if args.port_rest:
        logger.info("Starting REST api server on http://%s:%s" % (args.host, args.port_rest))
        try:
            rest_api = load_class_from_path(settings.REST_SERVER)
        except ValueError as err:
            logger.error(err)
            sys.exit()
        api_server_rest = rest_api()
        endpoint_rest = "tcp:port={0}:interface={1}".format(args.port_rest, args.host)
        endpoints.serverFromString(reactor, endpoint_rest).listen(Site(api_server_rest.app.resource()))

    reactor.addSystemEventTrigger('before', 'shutdown', stop_block_persisting)
    reactor.run()

    # After the reactor is stopped, gracefully shutdown the database.
    logger.info("Closing databases...")
    NotificationDB.close()
    Blockchain.Default().Dispose()
    NodeLeader.Instance().Shutdown()
    if wallet:
        wallet.Close()


if __name__ == "__main__":
    main()
