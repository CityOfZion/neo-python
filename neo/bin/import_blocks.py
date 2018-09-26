#!/usr/bin/env python3

from neo.Core.Blockchain import Blockchain
from neo.Core.Block import Block
from neo.IO.MemoryStream import MemoryStream
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Implementations.Blockchains.LevelDB.DBPrefix import DBPrefix
from neo.Settings import settings
from neocore.IO.BinaryReader import BinaryReader
from neocore.IO.BinaryWriter import BinaryWriter
from neo.IO.MemoryStream import StreamManager, MemoryStream
import argparse
import os
import shutil
from tqdm import trange
from prompt_toolkit import prompt
from neo.Implementations.Notifications.LevelDB.NotificationDB import NotificationDB


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
        raise Exception("Please specify an input path")
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

        if append:
            blockchain = LevelDBBlockchain(settings.chain_leveldb_path, skip_header_check=True)
            Blockchain.RegisterBlockchain(blockchain)

            start_block = Blockchain.Default().Height
            print("Starting import at %s " % start_block)
        else:
            print("Will import %s of %s blocks to %s" % (total_blocks, total_blocks_available, target_dir))
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

        if store_notifications:
            NotificationDB.instance().start()

        stream = MemoryStream()
        reader = BinaryReader(stream)
        block = Block()
        length_ba = bytearray(4)

        for index in trange(total_blocks, desc='Importing Blocks', unit=' Block'):
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
                chain.AddBlockDirectly(block, do_persist_complete=store_notifications)

            # reset blockheader
            block._header = None
            block.__hash = None

            # reset stream
            reader.stream.Cleanup()

    print("Wrote blocks.  Now writing headers")

    chain = Blockchain.Default()

    # reset header hash list
    chain._db.delete(DBPrefix.IX_HeaderHashList)

    total = len(header_hash_list)

    chain._header_index = header_hash_list

    print("storing header hash list...")

    while total - 2000 >= chain._stored_header_count:
        ms = StreamManager.GetStream()
        w = BinaryWriter(ms)
        headers_to_write = chain._header_index[chain._stored_header_count:chain._stored_header_count + 2000]
        w.Write2000256List(headers_to_write)
        out = ms.ToArray()
        StreamManager.ReleaseStream(ms)
        with chain._db.write_batch() as wb:
            wb.put(DBPrefix.IX_HeaderHashList + chain._stored_header_count.to_bytes(4, 'little'), out)

        chain._stored_header_count += 2000

    last_index = len(header_hash_list)
    chain._db.put(DBPrefix.SYS_CurrentHeader, header_hash_list[-1] + last_index.to_bytes(4, 'little'))

    print("Imported %s blocks to %s " % (total_blocks, target_dir))


if __name__ == "__main__":
    main()
