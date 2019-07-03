import plyvel
from neo.EventHub import events
from neo.SmartContract.SmartContractEvent import SmartContractEvent, NotifyEvent, NotifyType
from neo.Storage.Implementation.DBFactory import getNotificationDB
from neo.Storage.Interface.DBProperties import DBProperties
from neo.Core.State.ContractState import ContractState
from neo.Settings import settings
from neo.Core.Blockchain import Blockchain
from neo.Core.Helper import Helper
from neo.Core.UInt160 import UInt160
from neo.logging import log_manager

logger = log_manager.getLogger('db')


class NotificationPrefix:
    """
    Byte Prefixes to use for writing event data to disk
    """
    PREFIX_ADDR = b'\xCA'
    PREFIX_CONTRACT = b'\xCB'
    PREFIX_BLOCK = b'\xCC'

    PREFIX_COUNT = b'\xCD'

    PREFIX_TOKEN = b'\xCE'


class NotificationDB:
    __instance = None

    _events_to_write = None
    _new_contracts_to_write = None

    @staticmethod
    def instance():
        """
        Singleton accessor for NotificationDB
        Returns:
            NotificationDB: The current instance of the NotificationDB
        """
        if not NotificationDB.__instance:
            if settings.NOTIFICATION_DB_PATH:
                NotificationDB.__instance = NotificationDB(settings.notification_leveldb_path)
            else:
                logger.info("Notification DB Path not configured in settings")
        return NotificationDB.__instance

    @staticmethod
    def close():
        """
        Closes the database if it is open
        """
        if NotificationDB.__instance:
            NotificationDB.__instance.db.closeDB()
            NotificationDB.__instance = None

    @property
    def db(self):
        return self._db

    @property
    def current_events(self):
        """
        A list of events to be persisted in the next 'on_persist_complete' routine
        Returns:
            list: a list of events to write
        """
        return self._events_to_write + self._new_contracts_to_write

    def __init__(self, path):

        try:
            self._db = getNotificationDB(path)
        except Exception as e:
            logger.info("Notification leveldb unavailable, you may already be running this process: %s " % e)
            raise Exception('Notification Leveldb Unavailable %s ' % e)

    def start(self):
        """
        Handle EventHub events for SmartContract decorators
        """
        self._events_to_write = []
        self._new_contracts_to_write = []

        @events.on(SmartContractEvent.CONTRACT_CREATED)
        @events.on(SmartContractEvent.CONTRACT_MIGRATED)
        def call_on_success_event(sc_event: SmartContractEvent):
            self.on_smart_contract_created(sc_event)

        @events.on(SmartContractEvent.RUNTIME_NOTIFY)
        def call_on_event(sc_event: NotifyEvent):
            self.on_smart_contract_event(sc_event)

        Blockchain.Default().PersistCompleted.on_change += self.on_persist_completed

    def on_smart_contract_created(self, sc_event: SmartContractEvent):
        """
        Listener for SmartContractEvent
        Args:
            sc_event (SmartContractEvent): event to check and see if it contains NEP5Token created
        """
        if isinstance(sc_event.contract, ContractState):
            if not sc_event.test_mode:
                sc_event.CheckIsNEP5()
                if sc_event.token:
                    self._new_contracts_to_write.append(sc_event)

    def on_smart_contract_event(self, sc_event: NotifyEvent):
        """
        Listener for NotifyEvent
        Args:
            sc_event (NotifyEvent): event to check whether it should be persisted
        """
        if not isinstance(sc_event, NotifyEvent):
            logger.info("Not Notify Event instance")
            return
        if sc_event.ShouldPersist:
            if sc_event.notify_type in [NotifyType.TRANSFER, NotifyType.REFUND, NotifyType.MINT]:
                self._events_to_write.append(sc_event)

    def on_persist_completed(self, block):
        """
        Called when a block has been persisted to disk.  Used as a hook to persist notification data.
        Args:
            block (neo.Core.Block): the currently persisting block
        """
        if len(self._events_to_write):

            addr_db = self.db.getPrefixedDB(NotificationPrefix.PREFIX_ADDR)
            block_db = self.db.getPrefixedDB(NotificationPrefix.PREFIX_BLOCK)
            contract_db = self.db.getPrefixedDB(NotificationPrefix.PREFIX_CONTRACT)

            block_count = 0
            block_bytes = self._events_to_write[0].block_number.to_bytes(4, 'little')

            with block_db.getBatch() as block_write_batch:
                with contract_db.getBatch() as contract_write_batch:
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

                        with addr_db.getBatch() as b:
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

                        # write the event to the per-contract database
                        contract_bytes = bytes(evt.contract_hash.Data)
                        count_for_contract = contract_db.get(contract_bytes + NotificationPrefix.PREFIX_COUNT)
                        if not count_for_contract:
                            count_for_contract = b'\x00'
                        contract_event_key = contract_bytes + count_for_contract
                        contract_count_int = int.from_bytes(count_for_contract, 'little') + 1
                        new_contract_count = contract_count_int.to_bytes(4, 'little')
                        contract_write_batch.put(contract_bytes + NotificationPrefix.PREFIX_COUNT, new_contract_count)
                        contract_write_batch.put(contract_event_key, hash_data)

        self._events_to_write = []

        if len(self._new_contracts_to_write):

            token_db = self.db.getPrefixedDB(NotificationPrefix.PREFIX_TOKEN)

            with token_db.getBatch() as token_write_batch:
                for token_event in self._new_contracts_to_write:
                    try:
                        hash_data = token_event.ToByteArray()  # used to fail here
                        hash_key = token_event.contract.Code.ScriptHash().ToBytes()
                        token_write_batch.put(hash_key, hash_data)
                    except Exception as e:
                        logger.debug(f"Failed to write new contract, reason: {e}")

        self._new_contracts_to_write = []

    def get_by_block(self, block_number):
        """
        Look up notifications for a block
        Args:
            block_number (int): height of block to search for notifications

        Returns:
            list: a list of notifications
        """
        blocklist_snapshot = self.db.getPrefixedDB(NotificationPrefix.PREFIX_BLOCK).createSnapshot()

        block_bytes = block_number.to_bytes(4, 'little')
        results = []
        with blocklist_snapshot.db.openIter(DBProperties(prefix=block_bytes, include_key=False)) as it:
            for val in it:
                event = SmartContractEvent.FromByteArray(val)
                results.append(event)

        return results

    def get_by_addr(self, address):
        """
        Lookup a set of notifications by address
        Args:
            address (UInt160 or str): hash of address for notifications

        Returns:
            list: a list of notifications
        """
        addr = address
        if isinstance(address, str) and len(address) == 34:
            addr = Helper.AddrStrToScriptHash(address)

        if not isinstance(addr, UInt160):
            raise Exception("Incorrect address format")

        addrlist_snapshot = self.db.getPrefixedDB(NotificationPrefix.PREFIX_ADDR).createSnapshot()
        results = []

        with addrlist_snapshot.db.openIter(DBProperties(prefix=bytes(addr.Data), include_key=False)) as it:
            for val in it:
                if len(val) > 4:
                    try:
                        event = SmartContractEvent.FromByteArray(val)
                        results.append(event)
                    except Exception as e:
                        logger.error("could not parse event: %s %s" % (e, val))
        return results

    def get_by_contract(self, contract_hash):
        """
        Look up a set of notifications by the contract they are associated with
        Args:
            contract_hash (UInt160 or str): hash of contract for notifications to be retreived

        Returns:
            list: a list of notifications
        """
        hash = contract_hash
        if isinstance(contract_hash, str) and len(contract_hash) == 40:
            hash = UInt160.ParseString(contract_hash)

        if not isinstance(hash, UInt160):
            raise Exception("Incorrect address format")

        contractlist_snapshot = self.db.getPrefixedDB(NotificationPrefix.PREFIX_CONTRACT).createSnapshot()
        results = []

        with contractlist_snapshot.db.openIter(DBProperties(prefix=bytes(hash.Data), include_key=False)) as it:
            for val in it:
                if len(val) > 4:
                    try:
                        event = SmartContractEvent.FromByteArray(val)
                        results.append(event)
                    except Exception as e:
                        logger.error("could not parse event: %s %s" % (e, val))
        return results

    def get_tokens(self):
        """
        Looks up all tokens
        Returns:
            list: A list of smart contract events with contracts that are NEP5 Tokens
        """
        tokens_snapshot = self.db.getPrefixedDB(NotificationPrefix.PREFIX_TOKEN).createSnapshot()
        results = []

        with tokens_snapshot.db.openIter(DBProperties(include_key=False)) as it:
            for val in it:
                event = SmartContractEvent.FromByteArray(val)
                results.append(event)
        return results

    def get_token(self, hash):
        """
        Looks up a token by hash
        Args:
            hash (UInt160): The token to look up

        Returns:
            SmartContractEvent: A smart contract event with a contract that is an NEP5 Token
        """
        tokens_snapshot = self.db.getPrefixedDB(NotificationPrefix.PREFIX_TOKEN).createSnapshot()

        try:
            val = tokens_snapshot.db.get(hash.ToBytes())
            if val:
                event = SmartContractEvent.FromByteArray(val)
                return event
        except Exception as e:
            logger.error("Smart contract event with contract hash %s not found: %s " % (hash.ToString(), e))
        return None
