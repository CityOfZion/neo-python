#!/usr/bin/env python3

from neo.Core.Blockchain import Blockchain
from neo.Core.Block import Block
from neo.Storage.Implementation.DBFactory import getBlockchainDB
from neo.Settings import settings
from neo.Core.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream
import argparse
import os
import shutil
from tqdm import trange
from prompt_toolkit import prompt
from neo.Implementations.Notifications.NotificationDB import NotificationDB
import asyncio


def main():
    # needed for console scripts
    asyncio.run(_main())


async def _main():
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

    parser.add_argument("-n", "--notifications", help="Persist Notifications to database", default=False, action="store_true")

    parser.add_argument("-a", "--append", action="store_true", default=False, help="Append to current Block database")

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
        print("Please specify an input path")
        return
    file_path = args.input

    append = False
    store_notifications = False

    start_block = 0

    if args.append:
        append = True

    if args.notifications:
        store_notifications = True

    header_hash_list = []

    with open(file_path, 'rb') as file_input:

        total_blocks_available = int.from_bytes(file_input.read(4), 'little')

        if total_blocks_available == 0:
            total_blocks_available = int.from_bytes(file_input.read(4), 'little')

        total_blocks = total_blocks_available
        if args.totalblocks and args.totalblocks < total_blocks and args.totalblocks > 0:
            total_blocks = args.totalblocks

        target_dir = os.path.join(settings.DATA_DIR_PATH, settings.LEVELDB_PATH)
        notif_target_dir = os.path.join(settings.DATA_DIR_PATH, settings.NOTIFICATION_DB_PATH)

        stream = MemoryStream()
        reader = BinaryReader(stream)
        block = Block()
        length_ba = bytearray(4)
        ctr = 0

        if append:
            blockchain = Blockchain(getBlockchainDB(settings.chain_leveldb_path), skip_header_check=False)
            Blockchain.DeregisterBlockchain()
            Blockchain.RegisterBlockchain(blockchain)

            start_block = Blockchain.Default().Height
            print("Starting import at %s " % start_block)

            if args.totalblocks:
                total_blocks = args.totalblocks

            for _ in trange(start_block, desc='Skipping blocks', unit='Block'):
                file_input.readinto(length_ba)
                block_len = int.from_bytes(length_ba, 'little')
                file_input.seek(block_len, 1)
                ctr += 1
        else:
            print("Will import %s of %s blocks to %s" % (total_blocks, total_blocks_available, target_dir))
            print("This will overwrite any data currently in %s and %s.\nType 'confirm' to continue" % (target_dir, notif_target_dir))

            try:
                confirm = prompt("[confirm]> ", is_password=False)
            except KeyboardInterrupt:
                confirm = False
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
            blockchain = Blockchain(getBlockchainDB(settings.chain_leveldb_path))
            Blockchain.DeregisterBlockchain()
            Blockchain.RegisterBlockchain(blockchain)

            start_block = Blockchain.Default().Height

        chain = Blockchain.Default()

        if store_notifications:
            NotificationDB.instance().start()

        if start_block == 0:
            # set stream data
            file_input.readinto(length_ba)
            block_len = int.from_bytes(length_ba, 'little')

            reader.stream.write(file_input.read(block_len))
            reader.stream.seek(0)

            # get block
            block.DeserializeForImport(reader)
            header_hash_list.append(block.Hash.ToBytes())

            # add
            if block.Index > start_block:
                chain.AddHeaders([block.Header])
                await chain.TryPersist(block)

            # reset blockheader
            block._header = None
            block.__hash = None

            # reset stream
            reader.stream.Cleanup()

        for index in trange(total_blocks, desc='Importing Blocks', unit=' Block', initial=ctr):
            # set stream data
            file_input.readinto(length_ba)
            block_len = int.from_bytes(length_ba, 'little')

            reader.stream.write(file_input.read(block_len))
            reader.stream.seek(0)

            # get block
            block.DeserializeForImport(reader)
            header_hash_list.append(block.Hash.ToBytes())

            # add
            if block.Index >= start_block:
                chain.AddHeaders([block.Header])
                await chain.TryPersist(block)

            # reset blockheader
            block._header = None
            block.__hash = None

            # reset stream
            reader.stream.Cleanup()

    print("Imported %s blocks to %s " % (total_blocks, target_dir))


if __name__ == "__main__":
    main()
