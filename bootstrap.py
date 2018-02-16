from neo.Settings import settings
from neo.Prompt.Commands.Bootstrap import BootstrapBlockchainFile
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mainnet", action="store_true", default=False,
                        help="use MainNet instead of the default TestNet")
    parser.add_argument("-c", "--config", action="store", help="Use a specific config file")

    parser.add_argument("-n", "--notifications", action="store_true", default=False, help="Bootstrap notification dataase")

    args = parser.parse_args()

    if args.mainnet and args.config:
        print("Cannot use both --config and --mainnet parameters, please use only one.")
        exit(1)

    # Setup depending on command line arguments. By default, the testnet settings are already loaded.
    if args.config:
        settings.setup(args.config)
    elif args.mainnet:
        settings.setup_mainnet()

    if args.notifications:
        BootstrapBlockchainFile(settings.NOTIFICATION_DB_PATH, settings.NOTIF_BOOTSTRAP_FILE)
    else:
        BootstrapBlockchainFile(settings.LEVELDB_PATH, settings.BOOTSTRAP_FILE)


if __name__ == "__main__":
    main()
