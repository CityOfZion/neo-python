import plyvel
from logzero import logger
from neo.EventHub import events
from neo.SmartContract.SmartContractEvent import SmartContractEvent, NotifyEvent, NotifyType
from neo.Settings import settings
from neo.Core.Blockchain import Blockchain
from neo.Core.Helper import Helper
from neocore.UInt160 import UInt160
import json
import pdb


class NotificationPrefix():

    PREFIX_ADDR = b'\xCA'
#    PREFIX_CONTRACT = b'\xCB'
    PREFIX_BLOCK = b'\xCC'

    PREFIX_COUNT = b'\xCD'


class NotificationDB():

    __instance = None

    _events_to_write = None

    @staticmethod
    def instance():
        if not NotificationDB.__instance:
            if settings.NOTIFICATION_DB_PATH:
                NotificationDB.__instance = NotificationDB(settings.NOTIFICATION_DB_PATH)
#                logger.info("Created Notification DB At %s " % settings.NOTIFICATION_DB_PATH)
            else:
                logger.info("Notification DB Path not configured in settings")
        return NotificationDB.__instance

    @staticmethod
    def close():
        if NotificationDB.__instance:
            NotificationDB.__instance.db.close()
            NotificationDB.__instance = None

    @property
    def db(self):
        return self._db

    @property
    def current_events(self):
        return self._events_to_write

    def __init__(self, path):

        try:
            self._db = plyvel.DB(path, create_if_missing=True)
            logger.info("Created Notification DB At %s " % path)
        except Exception as e:
            logger.info("Notification leveldb unavailable, you may already be running this process: %s " % e)
            raise Exception('Notification Leveldb Unavailable %s ' % e)

    def start(self):
        # Handle EventHub events for SmartContract decorators
        self._events_to_write = []

        @events.on(SmartContractEvent.RUNTIME_NOTIFY)
        def call_on_event(sc_event: NotifyEvent):
            self.on_smart_contract_event(sc_event)
#            elif sc_event.notify_type == NotifyType.TRANSFER and sc_event.test_mode:
#                data = sc_event.ToByteArray()
#                event = SmartContractEvent.FromByteArray(data)
#                print("event? %s " % event)

        Blockchain.Default().PersistCompleted.on_change += self.on_persist_completed

    def on_smart_contract_event(self, sc_event: NotifyEvent):
        if not isinstance(sc_event, NotifyEvent):
            logger.info("Not Notify Event instance")
            return
        if sc_event.ShouldPersist and sc_event.notify_type == NotifyType.TRANSFER:
            self._events_to_write.append(sc_event)

    def on_persist_completed(self, block):
        if len(self._events_to_write):

            addr_db = self.db.prefixed_db(NotificationPrefix.PREFIX_ADDR)
            block_db = self.db.prefixed_db(NotificationPrefix.PREFIX_BLOCK)

            block_write_batch = block_db.write_batch()

            block_count = 0
            block_bytes = self._events_to_write[0].block_number.to_bytes(4, 'little')

            for evt in self._events_to_write:  # type:NotifyEvent

                # write the event for both or one of the addresses involved in the transfer
                write_both = True
                hash_data = evt.ToByteArray()

                bytes_to = bytes(evt.addr_to.Data)
                bytes_from = bytes(evt.addr_from.Data)

                if bytes_to == bytes_from:
                    write_both = False

                total_bytes_to = addr_db.get(bytes_to + NotificationPrefix.PREFIX_COUNT)
                total_bytes_from = addr_db.get(bytes_from + NotificationPrefix.PREFIX_COUNT)

                if not total_bytes_to:
                    total_bytes_to = b'\x00'

                if not total_bytes_from:
                    total_bytes_from = b'x\00'

                addr_to_key = bytes_to + total_bytes_to
                addr_from_key = bytes_from + total_bytes_from

                with addr_db.write_batch() as b:
                    b.put(addr_to_key, hash_data)
                    if write_both:
                        b.put(addr_from_key, hash_data)
                    total_bytes_to = int.from_bytes(total_bytes_to, 'little') + 1
                    total_bytes_from = int.from_bytes(total_bytes_from, 'little') + 1
                    new_bytes_to = total_bytes_to.to_bytes(4, 'little')
                    new_bytes_from = total_bytes_from.to_bytes(4, 'little')
                    b.put(bytes_to + NotificationPrefix.PREFIX_COUNT, new_bytes_to)
                    if write_both:
                        b.put(bytes_from + NotificationPrefix.PREFIX_COUNT, new_bytes_from)

                # write the event to the per-block database
                per_block_key = block_bytes + block_count.to_bytes(4, 'little')
                block_write_batch.put(per_block_key, hash_data)
                block_count += 1

            # finish off the per-block write batch
            block_write_batch.write()

        self._events_to_write = []

    def get_by_block(self, block_number):

        blocklist_snapshot = self.db.prefixed_db(NotificationPrefix.PREFIX_BLOCK).snapshot()
        block_bytes = block_number.to_bytes(4, 'little')
        results = []
        for val in blocklist_snapshot.iterator(prefix=block_bytes, include_key=False):
            event = SmartContractEvent.FromByteArray(val)
            results.append(event)

        return results

    def get_by_addr(self, address):
        addr = address
        if isinstance(address, str) and len(address) == 34:
            addr = Helper.AddrStrToScriptHash(address)

        if not isinstance(addr, UInt160):
            raise Exception("Incorrect address format")

        addrlist_snapshot = self.db.prefixed_db(NotificationPrefix.PREFIX_ADDR).snapshot()
        results = []

        for val in addrlist_snapshot.iterator(prefix=bytes(addr.Data), include_key=False):
            if len(val) > 4:
                try:
                    event = SmartContractEvent.FromByteArray(val)
                    results.append(event)
                except Exception as e:
                    logger.info("could not parse event: %s " % val)
        return results
