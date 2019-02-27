from contextlib import suppress

from neo.Core.Block import Block as OrigBlock
from neo.Core.Blockchain import Blockchain as BC
from neo.Network.neonetwork.common import msgrouter
from neo.Network.neonetwork.common.singleton import Singleton
from neo.logging import log_manager

logger = log_manager.getLogger('network')


class MemPool(Singleton):
    def init(self):
        self.pool = dict()
        msgrouter.on_block_persisted += self.update_pool_for_block_persist

    def add_transaction(self, tx) -> bool:
        if BC.Default() is None:
            return False

        if tx.Hash.ToString() in self.pool.keys():
            return False

        if BC.Default().ContainsTransaction(tx.Hash):
            return False

        if not tx.Verify(self.pool.values()):
            logger.error("Verifying tx result... failed")
            return False

        self.pool[tx.Hash] = tx

        return True

    def update_pool_for_block_persist(self, orig_block: OrigBlock) -> None:
        for tx in orig_block.Transactions:
            with suppress(KeyError):
                self.pool.pop(tx.Hash)
                logger.debug(f"Found {tx.Hash} in last persisted block. Removing from mempool")

    def reset(self) -> None:
        self.pool = dict()
