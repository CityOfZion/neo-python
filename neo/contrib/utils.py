import time
from threading import Event

from neo.Core.Blockchain import Blockchain
from neo.Core.TX.Transaction import Transaction
from neocore.UInt256 import UInt256


class TxNotFoundInBlockchainError(Exception):
    pass


def wait_for_tx(self, tx, max_seconds=120):
    """ Wait for tx to show up on blockchain

    Args:
        tx (Transaction or UInt256 or str): Transaction or just the hash
        max_seconds (float): maximum seconds to wait for tx to show up. default: 120

    Returns:
        True: if transaction was found

    Raises:
        AttributeError: if supplied tx is not Transaction or UInt256 or str
        TxNotFoundInBlockchainError: if tx is not found in blockchain after max_seconds
    """
    tx_hash = None
    if isinstance(tx, (str, UInt256)):
        tx_hash = str(tx)
    elif isinstance(tx, Transaction):
        tx_hash = tx.Hash.ToString()
    else:
        raise AttributeError("Supplied tx is type '%s', but must be Transaction or UInt256 or str" % type(tx))

    wait_event = Event()
    time_start = time.time()

    while True:
        # Try to find transaction in blockchain
        _tx, height = Blockchain.Default().GetTransaction(tx_hash)
        if height > -1:
            return True

        # Using a wait event for the delay because it is not blocking like time.sleep()
        wait_event.wait(3)

        seconds_passed = time.time() - time_start
        if seconds_passed > max_seconds:
            raise TxNotFoundInBlockchainError("Transaction with hash %s not found after %s seconds" % (tx_hash, int(seconds_passed)))
