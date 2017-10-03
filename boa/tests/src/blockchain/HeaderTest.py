from boa.blockchain.vm.Neo.Blockchain import GetHeader
from boa.blockchain.vm.Neo.Header import GetMerkleRoot,GetTimestamp,GetHash,GetVersion

from boa.blockchain.vm.Neo.Runtime import Notify,Log


def Main(block_height):

    header = GetHeader(block_height)

    Log("got header")

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

    if ts == 1494640540:

        return 9


    return a
