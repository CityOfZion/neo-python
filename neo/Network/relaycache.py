from contextlib import suppress

from neo.Core.Block import Block as OrigBlock
from neo.Network.common import msgrouter
from neo.Network.common.singleton import Singleton
from neo.logging import log_manager

logger = log_manager.getLogger('network')


# TODO: how can we tell if our item is rejected by consensus nodes other than not being processed after x time? cache can grow infinite in size

class RelayCache(Singleton):
    def init(self):
        self.cache = dict()  # uint256 : tx/block/consensus data
        msgrouter.on_block_persisted += self.update_cache_for_block_persist

    def add(self, old_style_inventory) -> None:
        # TODO: make this UInt256 instead of the string identifier once we've fully moved to the new implementation
        self.cache.update({old_style_inventory.Hash.ToString(): old_style_inventory})

    def get_and_remove(self, new_style_hash):
        try:
            return self.cache.pop(new_style_hash.to_string())
        except KeyError:
            return None

    def try_get(self, new_style_hash):
        return self.cache.get(new_style_hash.to_string(), None)

    def update_cache_for_block_persist(self, orig_block: OrigBlock) -> None:
        for tx in orig_block.Transactions:
            with suppress(KeyError):
                self.cache.pop(tx.Hash.ToString())
                logger.debug(f"Found {tx.Hash} in last persisted block. Removing from relay cache")

    def reset(self) -> None:
        self.cache = dict()
