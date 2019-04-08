#!/usr/bin/env python3
"""
This cli utility will be installed as `np-utils`. You can see the help with `np-utils -h`.
"""
import sys
import argparse
import base58
import hashlib
import json
import binascii

from Crypto import Random

from neo import __version__
from neo.Core.Cryptography.Crypto import Crypto
from neo.Core.UInt160 import UInt160
from neo.Core.KeyPair import KeyPair


class ConversionError(Exception):
    pass


def address_to_scripthash(address):
    data = bytes(base58.b58decode(address))

    # Make sure signature byte is correct. In python 3, data[0] is bytes, and in 2 it's str.
    # We use this isinstance checke to make it work with both Python 2 and 3.
    is_correct_signature = data[0] != 0x17 if isinstance(data[0], bytes) else b'\x17'
    if not is_correct_signature:
        raise ConversionError("Invalid address: wrong signature byte")

    # Make sure the checksum is correct
    if data[-4:] != hashlib.sha256(hashlib.sha256(data[:-4]).digest()).digest()[:4]:
        raise ConversionError("Invalid address: invalid checksum")

    # Return only the scripthash bytes
    return data[1:-4]


def scripthash_to_address(scripthash):
    try:
        if scripthash[0:2] != "0x":
            # litle endian. convert to big endian now.
            print("Detected little endian scripthash. Converting to big endian for internal use.")
            scripthash_bytes = binascii.unhexlify(scripthash)
            scripthash = "0x%s" % binascii.hexlify(scripthash_bytes[::-1]).decode("utf-8")
            print("Big endian scripthash:", scripthash)
        return Crypto.ToAddress(UInt160.ParseString(scripthash))
    except Exception as e:
        raise ConversionError("Wrong format")


def create_wallet():
    private_key = bytes(Random.get_random_bytes(32))
    keypair = KeyPair(priv_key=private_key)
    return {
        "private_key": keypair.Export(),
        "address": keypair.GetAddress()
    }


def main():
    parser = argparse.ArgumentParser()

    # Show the neo-python version
    parser.add_argument("--version", action="version",
                        version="neo-python v{version}".format(version=__version__))

    parser.add_argument("--address-to-scripthash", nargs=1, metavar="address",
                        help="Convert an address to scripthash")

    parser.add_argument("--scripthash-to-address", nargs=1, metavar="scripthash",
                        help="Convert scripthash to address")

    parser.add_argument("--create-wallet", action="store_true", help="Create a wallet")

    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        exit(1)

    # print(args)
    if args.address_to_scripthash:
        try:
            scripthash = address_to_scripthash(args.address_to_scripthash[0])
            print("Scripthash big endian:  0x{}".format(scripthash[::-1].hex()))
            print("Scripthash little endian: {}".format(scripthash.hex(), scripthash))
            print("Scripthash neo-python format: {!r}".format(scripthash))

        except ConversionError as e:
            print(e)
            exit(1)

    if args.scripthash_to_address:
        try:
            address = scripthash_to_address(args.scripthash_to_address[0])
            print(address)
        except ConversionError as e:
            print(e)
            exit(1)

    if args.create_wallet:
        w = create_wallet()
        print(json.dumps(w, indent=2))


if __name__ == "__main__":
    main()
