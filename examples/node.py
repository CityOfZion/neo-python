"""
Minimal NEO node with custom code in a background thread.

It will log events from all smart contracts on the blockchain
as they are seen in the received blocks.
"""
import threading
from time import sleep

from logzero import logger
from twisted.internet import reactor, task

from neo.Network.NodeLeader import NodeLeader
from neo.Core.Blockchain import Blockchain
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Settings import settings


# If you want the log messages to also be saved in a logfile, enable the
# next line. This configures a logfile with max 10 MB and 3 rotations:
# settings.set_logfile("/tmp/logfile.log", max_bytes=1e7, backup_count=3)

token_style = None
start_height = None
start_dt = None

 def __init__(self):
        self.input_parser = InputParser()
        self.start_height = Blockchain.Default().Height
        self.start_dt = datetime.datetime.utcnow()

        self.token_style = Style.from_dict({
            "command": preferences.token_style['Command'],
            "neo": preferences.token_style['Neo'],
            "default": preferences.token_style['Default'],
            "number": preferences.token_style['Number'],
        })

        
def custom_background_code():
    """ Custom code run in a background thread.

    This function is run in a daemonized thread, which means it can be instantly killed at any
    moment, whenever the main thread quits. If you need more safety, don't use a  daemonized
    thread and handle exiting this thread in another way (eg. with signals and events).
    """
    while True:
        logger.info("Block %s / %s", str(Blockchain.Default().Height), str(Blockchain.Default().HeaderHeight))
        sleep(15)
def custom_background_details():
    """ Custom code run in a background thread.

    This function is run in a daemonized thread, which means it can be instantly killed at any
    moment, whenever the main thread quits. If you need more safety, don't use a  daemonized
    thread and handle exiting this thread in another way (eg. with signals and events).
    """
    while True:
        height = Blockchain.Default().Height
        headers = Blockchain.Default().HeaderHeight

        diff = height - self.start_height
        now = datetime.datetime.utcnow()
        difftime = now - self.start_dt

        mins = difftime / datetime.timedelta(minutes=1)
        secs = mins * 60

        bpm = 0
        tps = 0
        if diff > 0 and mins > 0:
            bpm = diff / mins
            tps = Blockchain.Default().TXProcessed / secs
        
        out = "Progress: %s / %s\n" % (height, headers)
        out += "Block-cache length %s\n" % Blockchain.Default().BlockCacheCount
        out += "Blocks since program start %s\n" % diff
        out += "Time elapsed %s mins\n" % mins
        out += "Blocks per min %s \n" % bpm
        out += "TPS: %s \n" % tps
        tokens = [("class:number", out)]
        #print_formatted_text(FormattedText(tokens), style=self.token_style)
        logger.info("Custom Block Info %s", tokens)
        sleep(15)
        
def show_state(self):
        height = Blockchain.Default().Height
        headers = Blockchain.Default().HeaderHeight

        diff = height - self.start_height
        now = datetime.datetime.utcnow()
        difftime = now - self.start_dt

        mins = difftime / datetime.timedelta(minutes=1)
        secs = mins * 60

        bpm = 0
        tps = 0
        if diff > 0 and mins > 0:
            bpm = diff / mins
            tps = Blockchain.Default().TXProcessed / secs

        out = "Progress: %s / %s\n" % (height, headers)
        out += "Block-cache length %s\n" % Blockchain.Default().BlockCacheCount
        out += "Blocks since program start %s\n" % diff
        out += "Time elapsed %s mins\n" % mins
        out += "Blocks per min %s \n" % bpm
        out += "TPS: %s \n" % tps
        tokens = [("class:number", out)]
        print_formatted_text(FormattedText(tokens), style=self.token_style)
		
def main():
    # Use TestNet
    settings.setup_testnet()

    # Setup the blockchain
    blockchain = LevelDBBlockchain(settings.chain_leveldb_path)
    Blockchain.RegisterBlockchain(blockchain)
    dbloop = task.LoopingCall(Blockchain.Default().PersistBlocks)
    dbloop.start(.1)
    NodeLeader.Instance().Start()

    # Start a thread with custom code
    d = threading.Thread(target=custom_background_code)
    d.setDaemon(True)  # daemonizing the thread will kill it when the main thread is quit
    d.start()

    d = threading.Thread(target=custom_background_details)
    d.setDaemon(True)  # daemonizing the thread will kill it when the main thread is quit
    d.start()
    
    # Run all the things (blocking call)
    reactor.run()
    logger.info("Shutting down.")


if __name__ == "__main__":
    main()
