import sys

from logzero import logger

from neo.Cryptography.Crypto import *
from neo.UInt160 import UInt160
from neo.UInt256 import UInt256


class MerkleTreeNode(object):
    Hash = None
    Parent = None
    LeftChild = None
    RightChild = None

    def __init__(self, hash=None):
        self.Hash = hash

    def IsLeaf(self):
        if not self.LeftChild and not self.RightChild:
            return True
        return False

    def IsRoot(self):
        return self.Parent is None

    def Size(self):
        return sys.getsizeof(self)


class MerkleTree(object):

    Root = None

    Depth = 0

    def __init__(self, hashes):
        self.Root = MerkleTree.__Build([MerkleTreeNode(hash) for hash in hashes])
        depth = 1
        i = self.Root
        while i.LeftChild is not None:
            depth = depth + 1
            i = i.LeftChild
        self.Depth = depth

    @staticmethod
    def __Build(leaves):
        if len(leaves) < 1:
            raise Exception('Leaves must have length')
        if len(leaves) == 1:
            return leaves[0]

        num_parents = int((len(leaves) + 1) / 2)
        parents = [MerkleTreeNode() for i in range(0, num_parents)]

        for i in range(0, num_parents):
            node = parents[i]
            node.LeftChild = leaves[i * 2]
            leaves[i * 2].Parent = node
            if(i * 2 + 1 == len(leaves)):
                node.RightChild = node.LeftChild
            else:
                node.RightChild = leaves[i * 2 + 1]
                leaves[i * 2 + 1].Parent = node

            hasharray = bytearray(node.LeftChild.Hash.ToArray() + node.RightChild.Hash.ToArray())
            node.Hash = UInt256(data=Crypto.Hash256(hasharray))

        return MerkleTree.__Build(parents)

    # < summary >
    # 计算根节点的值
    # < / summary >
    # < param name = "hashes" > 子节点列表 < / param >
    # < returns > 返回计算的结果 < / returns >
    @staticmethod
    def ComputeRoot(hashes):
        if not len(hashes):
            raise Exception('Hashes must have length')
        if len(hashes) == 1:
            return hashes[0]

        tree = MerkleTree(hashes)
        return tree.Root.Hash

    @staticmethod
    def __DepthFirstSearch(node, hashes):
        if node.LeftChild is None:
            hashes.add(node.Hash)
        else:
            MerkleTree.__DepthFirstSearch(node.LeftChild, hashes)
            MerkleTree.__DepthFirstSearch(node.RightChild, hashes)

    def ToHashArray(self):
        hashes = set()
        MerkleTree.__DepthFirstSearch(self.Root, hashes)
        return list(hashes)

    def Trim(self, flags):
        logger.info("Trimming!")
        flags = bytearray(flags)
        length = 1 << len(self.Depth - 1)
        while len(flags) < length:
            flags.append(0)

        MerkleTree.__TrimNode(self.Root, 0, self.Depth, flags)

    @staticmethod
    def __TrimNode(node, index, depth, flags):
        if depth == 1 or node.LeftChild is None:
            return

        if depth == 2:
            if not flags[index * 2] and not flags[index * 2 + 1]:
                node.LeftChild = None
                node.RightChild = None

        else:

            MerkleTree.__TrimNode(node.LeftChild, index * 2, depth - 1, flags)
            MerkleTree.__TrimNode(node.RightChild, index * 2, depth - 1, flags)

            if node.LeftChild.LeftChild is None and node.RightChild.RightChild is None:
                node.LeftChild = None
                node.RightChild = None
