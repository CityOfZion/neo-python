import sys
from .Crypto import *
from neo.Core.UInt256 import UInt256


class MerkleTreeNode(object):

    def __init__(self, hash=None):
        """
        Create an instance.

        Args:
            hash (bytes):
        """
        self.Hash = hash
        self.Parent = None
        self.LeftChild = None
        self.RightChild = None

    def IsLeaf(self):
        """
        If the node is a leaf.

        Returns:
            bool: True if node is a leaf. False, otherwise.
        """
        if not self.LeftChild and not self.RightChild:
            return True
        return False

    def IsRoot(self):
        """
        If the node is the root.

        Returns:
            bool: True if the root. False otherwise.
        """
        return self.Parent is None

    def Size(self):
        """
        Get the size of self in bytes.
        Returns:
            int: number of bytes.
        """
        return sys.getsizeof(self)


class MerkleTree(object):
    Root = None

    Depth = 0

    def __init__(self, hashes):
        """
        Crease an instance.
        Args:
            hashes (list): each hash is of bytearray type.
        """
        self.Root = MerkleTree.__Build([MerkleTreeNode(hash) for hash in hashes])
        depth = 1
        i = self.Root
        while i.LeftChild is not None:
            depth = depth + 1
            i = i.LeftChild
        self.Depth = depth

    @staticmethod
    def __Build(leaves):
        """
        Build the merkle tree.

        Args:
            leaves (list): items are of type MerkleTreeNode.

        Returns:
            MerkleTreeNode: the root node.

        Raises:
            ValueError: if the length of `leaves` is < 1
        """
        if len(leaves) < 1:
            raise ValueError('Leaves must have length')
        if len(leaves) == 1:
            return leaves[0]

        num_parents = int((len(leaves) + 1) / 2)
        parents = [MerkleTreeNode() for i in range(0, num_parents)]

        for i in range(0, num_parents):
            node = parents[i]
            node.LeftChild = leaves[i * 2]
            leaves[i * 2].Parent = node
            if (i * 2 + 1 == len(leaves)):
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
        """
        Compute the root hash.

        Args:
            hashes (list): the list of hashes to build the root from.

        Returns:
            bytes: the root hash.

        Raises:
            ValueError: if the `hashes` array is empty
        """
        if not len(hashes):
            raise ValueError('Hashes must have length')
        if len(hashes) == 1:
            return hashes[0]

        tree = MerkleTree(hashes)
        return tree.Root.Hash

    @staticmethod
    def __DepthFirstSearch(node, hashes):
        """
        Internal helper method.

        Args:
            node (MerkleTreeNode):
            hashes (list): each item is a bytearray.
        """
        if node.LeftChild is None:
            hashes.add(node.Hash)
        else:
            MerkleTree.__DepthFirstSearch(node.LeftChild, hashes)
            MerkleTree.__DepthFirstSearch(node.RightChild, hashes)

    def ToHashArray(self):
        """
        Turn the tree into a list of hashes.

        Returns:
            list:
        """
        hashes = set()
        MerkleTree.__DepthFirstSearch(self.Root, hashes)
        return list(hashes)

    def Trim(self, flags):
        """
        Trim the nodes from the tree keeping only the root hash.

        Args:
            flags: "0000" for trimming, any other value for keeping the nodes.
        """
        flags = bytearray(flags)
        length = 1 << self.Depth - 1
        while len(flags) < length:
            flags.append(0)

        MerkleTree._TrimNode(self.Root, 0, self.Depth, flags)

    @staticmethod
    def _TrimNode(node, index, depth, flags):
        """
        Internal helper method to trim a node.

        Args:
            node (MerkleTreeNode):
            index (int): flag index.
            depth (int): node tree depth to start trim from.
            flags (bytearray): of left/right pairs. 1 byte for the left node, 1 byte for the right node.
                                00 to erase, 11 to keep. Will keep the node if either left or right is not-0
        """
        if depth == 1 or node.LeftChild is None:
            return

        if depth == 2:
            if not flags[index * 2] and not flags[index * 2 + 1]:
                node.LeftChild = None
                node.RightChild = None

        else:

            MerkleTree._TrimNode(node.LeftChild, index * 2, depth - 1, flags)
            MerkleTree._TrimNode(node.RightChild, index * 2, depth - 1, flags)

            if node.LeftChild.LeftChild is None and node.RightChild.RightChild is None:
                node.LeftChild = None
                node.RightChild = None
