from boa.blockchain.vm.Neo.Blockchain import GetHeader
from boa.blockchain.vm.Neo.Header import *

from boa.blockchain.vm.Neo.Runtime import Notify,Log


def Main():

    block_height = 12536
    header = GetHeader(block_height)

    print("got header")

    merkle = GetMerkleRoot(header)

    version = GetVersion(header)

    Notify(version)

    hash = GetHash(header)

    Notify(hash)

    print("got merkle")

    Notify(header)

    a = 1

    Notify(merkle)


    print("getting timestamp")
    ts = GetTimestamp(header)

    Notify(ts)

    if ts == 1494640527:

        return 9


    return a
