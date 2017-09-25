from boa.blockchain.vm.Neo.Blockchain import GetBlock
from boa.blockchain.vm.Neo.Runtime import Notify,Log


def Main():

#    blockhash = b'\xe9F.\xbd\x83\x99\xb4\xa3Z\xdc\xdde\xe5^\xed\xf6\x9f\x82\xa3\x14\xc9y\x04\xb8\xfe\x8cb\xafO.\xe7\xd9'
    block_height = 123234
    block = GetBlock(block_height)

    print("hello")
    Notify(block)

    a = 1



    return block_height
