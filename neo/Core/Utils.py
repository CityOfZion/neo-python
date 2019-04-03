import base58


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
