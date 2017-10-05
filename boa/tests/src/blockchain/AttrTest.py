from boa.blockchain.vm.Neo.Blockchain import GetHeader,GetBlock
from boa.blockchain.vm.Neo.Block import GetTransaction
from boa.blockchain.vm.Neo.Runtime import Notify

def Main():


    height = 1242
    header = GetHeader(height)


    m2 = header.Timestamp + header.Timestamp

    root = header.MerkleRoot

#    Notify(root)

    hash = header.Hash

    prev = header.PrevHash

#    Notify(hash)

#    Notify(prev)


    bheight = 32566

    block = GetBlock(bheight)

    tx = block.Transactions[0]

    Notify(tx)

#    tx = GetTransaction(block, 0)
#    tx = GetTransaction(block, 0)
#    Notify(tx)
#    tx = block.Transactions[0] #  this doesnt seem to work
    txhash = tx.Hash

    Notify(txhash)

    return 1
