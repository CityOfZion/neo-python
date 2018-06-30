#!/usr/bin/env python3

from neo.Core.Blockchain import Blockchain
from neo.Core.Block import Block
from neo.IO.MemoryStream import MemoryStream
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Settings import settings
from neocore.IO.BinaryReader import BinaryReader
import argparse
import os
import shutil
from tqdm import trange
from prompt_toolkit import prompt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mainnet", action="store_true", default=False,
                        help="use MainNet instead of the default TestNet")
    parser.add_argument("-c", "--config", action="store", help="Use a specific config file")

    # Where to store stuff
    parser.add_argument("--datadir", action="store",
                        help="Absolute path to use for database directories")

    parser.add_argument("-i", "--input", help="Where the input file lives")

    parser.add_argument("-t", "--totalblocks", help="Total blocks to import", type=int)

    parser.add_argument("-l", "--logevents", help="Log Smart Contract Events", default=False, action="store_true")

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

    if args.logevents:
        settings.log_smart_contract_events = True

    if not args.input:
        raise Exception("Please specify an input path")
    file_path = args.input

    with open(file_path, 'rb') as file_input:

        total_blocks = int.from_bytes(file_input.read(4), 'little')

        target_dir = os.path.join(settings.DATA_DIR_PATH, settings.LEVELDB_PATH)
        notif_target_dir = os.path.join(settings.DATA_DIR_PATH, settings.NOTIFICATION_DB_PATH)

        print("Will import %s blocks to %s" % (total_blocks, target_dir))
        print("This will overwrite any data currently in %s and %s.\nType 'confirm' to continue" % (target_dir, notif_target_dir))

        confirm = prompt("[confirm]> ", is_password=False)
        if not confirm == 'confirm':
            print("Cancelled operation")
            return False

        try:
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            if os.path.exists(notif_target_dir):
                shutil.rmtree(notif_target_dir)
        except Exception as e:
            print("Could not remove existing data %s " % e)
            return False

        # Instantiate the blockchain and subscribe to notifications
        blockchain = LevelDBBlockchain(settings.chain_leveldb_path)
        Blockchain.RegisterBlockchain(blockchain)

        chain = Blockchain.Default()

        stream = MemoryStream()
        reader = BinaryReader(stream)
        block = Block()

        for index in trange(total_blocks, desc='Importing Blocks', unit=' Block'):
            # set stream data
            block_len = int.from_bytes(file_input.read(4), 'little')
            reader.stream.write(file_input.read(block_len))
            reader.stream.seek(0)

            # get block
            block.Deserialize(reader)

            # add
            if block.Index > 0:
                chain.AddBlockDirectly(block)

            # reset stream
            reader.stream.Cleanup()

    print("Imported %s blocks to %s " % (total_blocks, target_dir))


if __name__ == "__main__":
    main()
