#!/usr/bin/env python3

from neo.Settings import settings
from neo.Prompt.Commands.Bootstrap import BootstrapBlockchainFile
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mainnet", action="store_true", default=False,
                        help="use MainNet instead of the default TestNet")
    parser.add_argument("-c", "--config", action="store", help="Use a specific config file")

    parser.add_argument("-n", "--notifications", action="store_true", default=False,
                        help="Bootstrap notification database")

    parser.add_argument("-s", "--skipconfirm", action="store_true", default=False,
                        help="Bypass warning about overwritting data in {}".format(settings.LEVELDB_PATH))

    # Where to store stuff
    parser.add_argument("--datadir", action="store",
                        help="Absolute path to use for database directories")

    args = parser.parse_args()

    if args.mainnet and args.config:
        print("Cannot use both --config and --mainnet parameters, please use only one.")
        exit(1)

    if args.skipconfirm:
        require_confirm = False
    else:
        require_confirm = True

    # Setting the datadir must come before setting the network, else the wrong path is checked at net setup.
    if args.datadir:
        settings.set_data_dir(args.datadir)

    # Setup depending on command line arguments. By default, the testnet settings are already loaded.
    if args.config:
        settings.setup(args.config)
    elif args.mainnet:
        settings.setup_mainnet()

    destination_path = settings.chain_leveldb_path
    bootstrap_name = settings.BOOTSTRAP_NAME
    if args.notifications:
        bootstrap_name += "_notif"
        destination_path = settings.notification_leveldb_path

    BootstrapBlockchainFile(destination_path, settings.BOOTSTRAP_LOCATIONS, bootstrap_name, require_confirm)


if __name__ == "__main__":
    main()
