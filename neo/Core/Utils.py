import base58
from neo.Settings import settings
from neo.Core.Fixed8 import Fixed8
from typing import Tuple


def isValidPublicAddress(address: str) -> bool:
    """Check if address is a valid NEO address"""
    valid = False

    if len(address) == 34 and address[0] == 'A':
        try:
            base58.b58decode_check(address.encode())
            valid = True
        except ValueError:
            # checksum mismatch
            valid = False

    return valid


def validate_simple_policy(tx) -> Tuple[bool, str]:
    """
    Validate transaction policies

    Args:
        tx: Transaction object

    Returns:
        tuple:
            result: True if it passes the policy checks. False otherwise.
            error_msg: empty str if policy passes, otherwise reason for failure.
    """
    # verify the maximum tx size is not exceeded
    if tx.Size() > tx.MAX_TX_SIZE:
        return False, f"Transaction cancelled. The tx size ({tx.Size()}) exceeds the maximum tx size ({tx.MAX_TX_SIZE})."

    # calculate and verify the required network fee for the tx
    fee = tx.NetworkFee()
    if tx.Size() > settings.MAX_FREE_TX_SIZE and not tx.Type == b'\x02':  # Claim Transactions are High Priority
        req_fee = Fixed8.FromDecimal(settings.FEE_PER_EXTRA_BYTE * (tx.Size() - settings.MAX_FREE_TX_SIZE))
        if req_fee < settings.LOW_PRIORITY_THRESHOLD:
            req_fee = settings.LOW_PRIORITY_THRESHOLD
        if fee < req_fee:
            return False, f'Transaction cancelled. The tx size ({tx.Size()}) exceeds the max free tx size ({settings.MAX_FREE_TX_SIZE}).\nA network fee of {req_fee.ToString()} GAS is required.'
    return True, ""
