from neo.Network.core.blockbase import BlockBase
from neo.Network.core.header import Header
from neo.Network.core.io.binary_reader import BinaryReader
from neo.Network.core.io.binary_writer import BinaryWriter
from neo.Network.core.uint256 import UInt256
from typing import Union


class Block(BlockBase):
    def __init__(self, prev_hash, timestamp, index, consensus_data, next_consensus, witness):
        version = 0
        temp_merkleroot = UInt256.zero()
        super(Block, self).__init__(version, prev_hash, temp_merkleroot, timestamp, index, consensus_data, next_consensus, witness)
        self.prev_hash = prev_hash
        self.timestamp = timestamp
        self.index = index
        self.consensus_data = consensus_data
        self.next_consensus = next_consensus
        self.witness = witness
        self.transactions = []  # hardcoded to empty as we will not deserialize these

        # not part of the official Block implementation, just useful info for internal usage
        self._tx_count = 0
        self._size = 0

    def header(self) -> Header:
        return Header(self.prev_hash, self.merkle_root, self.timestamp, self.index, self.consensus_data,
                      self.next_consensus, self.witness)

    def serialize(self, writer: 'BinaryWriter') -> None:
        """ Serialize object. """
        super(Block, self).serialize(writer)

        len_transactions = len(self.transactions)
        if len_transactions == 0:
            writer.write_uint8(0)
        else:
            writer.write_var_int(len_transactions)
            for tx in self.transactions:
                tx.serialize(writer)

    def deserialize(self, reader: 'BinaryReader') -> None:
        """ Deserialize object. """
        super(Block, self).deserialize(reader)

        # ignore reading actual transactions, but we can determine the count
        self._tx_count = reader.read_var_int()

    @classmethod
    def deserialize_from_bytes(cls, data_stream: Union[bytes, bytearray]) -> 'Block':
        """ Deserialize object from a byte array. """
        br = BinaryReader(stream=data_stream)
        block = cls(None, None, None, None, None, None)
        try:
            block.deserialize(br)
            # at this point we do not fully support all classes that can build up a block (e.g. Transactions)
            # the normal size calculation would request each class for its size and sum them up
            # we can shortcut this calculation in the absence of those classes by just determining the amount of bytes
            # in the payload
            block._size = len(data_stream)
        except ValueError:
            return None
        finally:
            br.cleanup()
        return block

    def to_array(self) -> bytearray:
        writer = BinaryWriter(stream=bytearray())
        self.serialize(writer)
        data = bytearray(writer._stream.getvalue())
        writer.cleanup()
        return data
