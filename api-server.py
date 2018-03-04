#!/usr/bin/env python3
"""
This api server runs one or both of the json-rpc and rest api. Uses
neo.api.JSONRPC.JsonRpcApi and neo.api.REST.NotificationRestApi

See also:

* Tutorial on setting up an api server: https://gist.github.com/metachris/2be27cdff9503ebe7db1c27bfc60e435
* Example systemd service config: https://gist.github.com/metachris/03d1cc47df7cddfbc4009d5249bdfc6c
* JSON-RPC api issues: https://github.com/CityOfZion/neo-python/issues/273
"""
import os
import sys
import syslog
import argparse
import threading
from time import sleep
from twisted.python import log
from twisted.python.syslog import startLogging

import logzero
from logzero import logger
from twisted.internet import reactor, task, endpoints
from twisted.web.server import Site
from klein import Klein
from logging.handlers import SysLogHandler

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

# Logfile settings
LOGFILE_DEFAULT = os.path.join(DIR_PROJECT_ROOT, 'api-server.log')
LOGFILE_MAX_BYTES = 5e7  # 50 MB
LOGFILE_BACKUP_COUNT = 3  # 3 logfiles history

# Set the PID file
PID_FILE = "/tmp/neopython-api-server.pid"


def write_pid_file():
    """ Write a pid file, to easily kill the service """
    f = open(PID_FILE, "w")
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

    logfile = None
    syslog_facility = None
    if args.syslog or args.syslog_local:
        # Setup the syslog facility
        if args.syslog_local:
            print("Logging to syslog local facility %s", args.syslog_local)
            syslog_facility = SysLogHandler.LOG_LOCAL0 + args.syslog_local
        else:
            print("Logging to syslog user facility")
            syslog_facility = SysLogHandler.LOG_USER

        # Setup logzero to only use the syslog handler
        logzero.logfile(None, disableStderrLogger=args.disable_stderr)
        syslog_handler = SysLogHandler(facility=syslog_facility)
        logger.addHandler(syslog_handler)
    else:
        # Setup logzero logfile
        if args.logfile:
            log_fn = os.path.abspath(args.logfile)
            print("Logging to logfile: %s", log_fn)
            logfile = open(log_fn, "a")
            logzero.logfile(log_fn, maxBytes=LOGFILE_MAX_BYTES, backupCount=LOGFILE_BACKUP_COUNT, disableStderrLogger=args.disable_stderr)

        else:
            print("Logging to stdout and stderr")

    # Write a PID file to easily quit the service
    write_pid_file()

    # Instantiate the blockchain and subscribe to notifications
    blockchain = LevelDBBlockchain(settings.LEVELDB_PATH)
    Blockchain.RegisterBlockchain(blockchain)
    dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
    dbloop.start(.1)

    # Disable logging smart contract events
    settings.set_log_smart_contract_events(False)

    # Start the notification db instance
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

    if args.port_rpc:
        logger.info("Starting json-rpc api server on http://%s:%s" % (host, args.port_rpc))
        api_server_rpc = JsonRpcApi(args.port_rpc)
        endpoint_rpc = "tcp:port={0}:interface={1}".format(args.port_rpc, host)
        endpoints.serverFromString(reactor, endpoint_rpc).listen(Site(api_server_rpc.app.resource()))

    if args.port_rest:
        logger.info("Starting notification api server on http://%s:%s" % (host, args.port_rest))
        api_server_rest = NotificationRestApi()
        endpoint_rest = "tcp:port={0}:interface={1}".format(args.port_rest, host)
        endpoints.serverFromString(reactor, endpoint_rest).listen(Site(api_server_rest.app.resource()))

    app = ApiKlein()
    app.run(host, 9999, logFile=logfile, syslog_facility=syslog_facility)


class ApiKlein(Klein):
    """
    ApiKlein extends Klein so that the logging behavior can be customized. Aside from logging,
    the implementation is identical to Klein.run(): https://github.com/twisted/klein/blob/master/src/klein/_app.py#L376
    """
    def run(self, host=None, port=None, logFile=None, endpoint_description=None, syslog_facility=None):
        if syslog_facility is not None:
            facility = translate_syslog_facility(syslog_facility)
            startLogging(prefix="pyapi", facility=facility)

        elif logFile is not None:
            log.startLogging(logFile)

        else:
            log.startLogging(sys.stdout)

        if not endpoint_description:
            endpoint_description = "tcp:port={0}:interface={1}".format(port, host)

        endpoint = endpoints.serverFromString(reactor, endpoint_description)
        endpoint.listen(Site(self.resource()))
        reactor.run()


def translate_syslog_facility(syslog_facility):
    """
    SysLogHandler's facility is on a completely different scale than syslog, so
    this method translates between the two
    :param syslog_facility: the syslog facility value used by SysLogHandler
    :return: the syslog facility value used by syslog (and thus Klein's logger)
    """
    mapping = {
        SysLogHandler.LOG_USER: syslog.LOG_USER,
        SysLogHandler.LOG_LOCAL0: syslog.LOG_LOCAL0,
        SysLogHandler.LOG_LOCAL1: syslog.LOG_LOCAL1,
        SysLogHandler.LOG_LOCAL2: syslog.LOG_LOCAL2,
        SysLogHandler.LOG_LOCAL3: syslog.LOG_LOCAL3,
        SysLogHandler.LOG_LOCAL4: syslog.LOG_LOCAL4,
        SysLogHandler.LOG_LOCAL5: syslog.LOG_LOCAL5,
        SysLogHandler.LOG_LOCAL6: syslog.LOG_LOCAL6,
        SysLogHandler.LOG_LOCAL7: syslog.LOG_LOCAL7
    }

    if syslog_facility not in mapping:
        raise ValueError("Unsupported value for syslog_facility %s" % syslog_facility)

    return mapping[syslog_facility]


if __name__ == "__main__":
    main()
