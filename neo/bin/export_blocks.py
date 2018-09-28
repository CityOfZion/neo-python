#!/usr/bin/env python3

from neo.Settings import settings
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Core.Blockchain import Blockchain
import argparse
from tqdm import trange
import binascii
from neo.Core.Helper import Helper


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mainnet", action="store_true", default=False,
                        help="use MainNet instead of the default TestNet")
    parser.add_argument("-c", "--config", action="store", help="Use a specific config file")

    # Where to store stuff
    parser.add_argument("--datadir", action="store",
                        help="Absolute path to use for database directories")

    parser.add_argument("-o", "--output", help="Where to save output file")

    parser.add_argument("-t", "--totalblocks", help="Total blocks to export", type=int)

    args = parser.parse_args()

    if args.mainnet and args.config:
        print("Cannot use both --config and --mainnet parameters, please use only one.")
        exit(1)

    # Setting the datadir must come before setting the network, else the wrong path is checked at net setup.
    if args.datadir:
        settings.set_data_dir(args.datadir)

    # Setup depending on command line arguments. By default, the testnet settings are already loaded.
    if args.config:
        settings.setup(args.config)
    elif args.mainnet:
        settings.setup_mainnet()

    if not args.output:
        raise Exception("Please specify an output path")

    file_path = args.output

    # Instantiate the blockchain and subscribe to notifications
    blockchain = LevelDBBlockchain(settings.chain_leveldb_path)
    Blockchain.RegisterBlockchain(blockchain)

    chain = Blockchain.Default()

    with open(file_path, 'wb') as file_out:

        total = Blockchain.Default().Height - 1

        if args.totalblocks:
            total = args.totalblocks

        total_block_output = total.to_bytes(4, 'little')

        print("Using network %s " % settings.net_name)
        print("Will export %s blocks to %s " % (total, file_path))

        file_out.write(total_block_output)

        for index in trange(total, desc='Exporting blocks:', unit=' Block'):

            block = chain.GetBlockByHeight(index)
            block.LoadTransactions()

            # make sure this block has transactions
            # otherwise we will have a bad import
            if len(block.Transactions) < 1:
                raise Exception("Block %s has no transactions %s " % block.Index)

            output = Helper.ToStream(block)

            output_length = len(output).to_bytes(4, 'little')
            file_out.write(output_length)
            file_out.write(output)

    print("Exported %s blocks to %s " % (total, file_path))


if __name__ == "__main__":
    main()
