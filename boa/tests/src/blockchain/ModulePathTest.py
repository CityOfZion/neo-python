from boa.blockchain.vm.Neo.Runtime import Notify
from boa.blockchain.vm.Neo.Blockchain import GetHeader,GetBlock
from boa.blockchain.vm.Neo.Transaction import *

INVOKE_TX_TYPE=b'\xd1'

def Main(block_index):


    header = GetHeader(block_index)

    print("got block!")

    ts = header.Timestamp

    print("got timestamp")

    block = GetBlock(block_index)

    for tx in block.Transactions:


        type= GetType(tx)
        hash = GetHash(tx)
        Notify(type)
        is_invoke = False
        if type == INVOKE_TX_TYPE:
            is_invoke = True


        if hash == b'\xa0ljY\xd8n\x1b\xb5\xdb\xa0\xf5d\xd8\xb3\xd8\xec\xf2\xfb\xe3E\xe3|3\xba\x83\xf2$jW\xa24':
            print("correct hash!")
        else:
            print("hash does not match")




    return ts

