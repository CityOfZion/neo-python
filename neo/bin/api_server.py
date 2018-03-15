#!/usr/bin/env python3
"""
API server to run the JSON-RPC and REST API.

Uses neo.api.JSONRPC.JsonRpcApi and neo.api.REST.RestApi

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
import argparse
import threading
from time import sleep
from logging.handlers import SysLogHandler

import logzero
from logzero import logger

# Twisted logging
from twisted.logger import STDLibLogObserver, globalLogPublisher

# Twisted and Klein methods and modules
from twisted.internet import reactor, task, endpoints
from twisted.web.server import Site

# neo methods and modules
from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.api.JSONRPC.JsonRpcApi import JsonRpcApi
from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB
from neo.api.REST.RestApi import RestApi

from neo.Network.NodeLeader import NodeLeader
from neo.Settings import settings


# Logfile default settings (only used if --logfile arg is used)
LOGFILE_MAX_BYTES = 5e7  # 50 MB
LOGFILE_BACKUP_COUNT = 3  # 3 logfiles history

# Set the PID file, possible to override with env var PID_FILE
PID_FILE = os.getenv("PID_FILE", "/tmp/neopython-api-server.pid")


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
        logger.info("[%s] Block %s / %s", settings.net_name, str(Blockchain.Default().Height), str(Blockchain.Default().HeaderHeight))
        sleep(15)


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
    group_logging.add_argument("--syslog-local", action="store", type=int, choices=range(0, 7), metavar="[0-7]", help="Log to a local syslog facility instead of 'user'. Value must be between 0 and 7 (e.g. 0 for 'local0').")
    group_logging.add_argument("--disable-stderr", action="store_true", help="Disable stderr logger")

    # Where to store stuff
    parser.add_argument("--datadir", action="store",
                        help="Absolute path to use for database directories")

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

    # Setup depending on command line arguments. By default, the testnet settings are already loaded.
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

    if args.datadir:
        settings.set_data_dir(args.datadir)

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

    # Disable logging smart contract events
    settings.set_log_smart_contract_events(False)

    # Write a PID file to easily quit the service
    write_pid_file()

    # Setup Twisted and Klein logging to use the logzero setup
    observer = STDLibLogObserver(name=logzero.LOGZERO_DEFAULT_LOGGER)
    globalLogPublisher.addObserver(observer)

    # Instantiate the blockchain and subscribe to notifications
    blockchain = LevelDBBlockchain(settings.chain_leveldb_path)
    Blockchain.RegisterBlockchain(blockchain)
    dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
    dbloop.start(.1)

    # Setup twisted reactor, NodeLeader and start the NotificationDB
    reactor.suggestThreadPoolSize(15)
    NodeLeader.Instance().Start()
    NotificationDB.instance().start()

    # Start a thread with custom code
    d = threading.Thread(target=custom_background_code)
    d.setDaemon(True)  # daemonizing the thread will kill it when the main thread is quit
    d.start()

    # Default host is open for all
    host = "0.0.0.0"

    if args.port_rpc:
        logger.info("Starting json-rpc api server on http://%s:%s" % (host, args.port_rpc))
        api_server_rpc = JsonRpcApi(args.port_rpc)
        endpoint_rpc = "tcp:port={0}:interface={1}".format(args.port_rpc, host)
        endpoints.serverFromString(reactor, endpoint_rpc).listen(Site(api_server_rpc.app.resource()))

    if args.port_rest:
        logger.info("Starting REST api server on http://%s:%s" % (host, args.port_rest))
        api_server_rest = RestApi()
        endpoint_rest = "tcp:port={0}:interface={1}".format(args.port_rest, host)
        endpoints.serverFromString(reactor, endpoint_rest).listen(Site(api_server_rest.app.resource()))

    reactor.run()

    # After the reactor is stopped, gracefully shutdown the database.
    logger.info("Closing databases...")
    NotificationDB.close()
    Blockchain.Default().Dispose()
    NodeLeader.Instance().Shutdown()


if __name__ == "__main__":
    main()
