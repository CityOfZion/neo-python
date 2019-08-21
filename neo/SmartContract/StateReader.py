from neo.VM.InteropService import InteropService
from neo.SmartContract.Contract import Contract
from neo.SmartContract.NotifyEventArgs import NotifyEventArgs
from neo.Core.State.StorageKey import StorageKey
from neo.Blockchain import GetBlockchain
import neo.Core.BlockBase
import neo.Core.Block
import neo.Core.TX.Transaction
import neo.SmartContract.StorageContext
import neo.SmartContract.TriggerType as TriggerType
from neo.Core.Cryptography.Crypto import Crypto
from neo.Core.BigInteger import BigInteger
from neo.Core.UInt160 import UInt160
from neo.Core.UInt256 import UInt256
from neo.SmartContract.SmartContractEvent import SmartContractEvent, NotifyEvent
from neo.SmartContract.ContractParameter import ContractParameter, ContractParameterType
from neo.Core.Cryptography.ECCurve import ECDSA
from neo.VM.InteropService import StackItem, ByteArray, Array, Map
from neo.VM.ExecutionEngine import ExecutionEngine
from neo.Settings import settings
from neo.Core.IO.BinaryReader import BinaryReader
from neo.Core.IO.BinaryWriter import BinaryWriter
from neo.IO.MemoryStream import StreamManager
from neo.Core.State.ContractState import ContractState
from neo.Core.State.StorageItem import StorageItem
from neo.logging import log_manager
import hashlib

logger = log_manager.getLogger('vm')


class StateReader(InteropService):

    def RegisterWithPrice(self, method, func, price):
        hashed_method = int.from_bytes(hashlib.sha256(method.encode()).digest()[:4], 'little', signed=False)
        self._dictionary[hashed_method] = func
        self.prices.update({hashed_method: price})

    def __init__(self, trigger_type, snapshot):

        super(StateReader, self).__init__()
        self.Trigger = trigger_type
        self.Snapshot = snapshot

        self.notifications = []
        self.events_to_dispatch = []
        self.prices = {}
        self._hashes_for_verifying = None
        self._accounts = None
        self._assets = None
        self._contracts = None
        self._storages = None

        # TODO: move ExecutionEngine calls here as well from /neo/VM/InteropService/

        # Standard Library
        self.RegisterWithPrice("System.Runtime.Platform", self.Runtime_Platform, 1)
        self.RegisterWithPrice("System.Runtime.GetTrigger", self.Runtime_GetTrigger, 1)
        self.RegisterWithPrice("System.Runtime.CheckWitness", self.Runtime_CheckWitness, 200)
        self.RegisterWithPrice("System.Runtime.Notify", self.Runtime_Notify, 1)
        self.RegisterWithPrice("System.Runtime.Log", self.Runtime_Log, 1)
        self.RegisterWithPrice("System.Runtime.GetTime", self.Runtime_GetCurrentTime, 1)
        self.RegisterWithPrice("System.Runtime.Serialize", self.Runtime_Serialize, 1)
        self.RegisterWithPrice("System.Runtime.Deserialize", self.Runtime_Deserialize, 1)
        self.RegisterWithPrice("System.Blockchain.GetHeight", self.Blockchain_GetHeight, 1)
        self.RegisterWithPrice("System.Blockchain.GetHeader", self.Blockchain_GetHeader, 100)
        self.RegisterWithPrice("System.Blockchain.GetBlock", self.Blockchain_GetBlock, 200)
        self.RegisterWithPrice("System.Blockchain.GetTransaction", self.Blockchain_GetTransaction, 200)
        self.RegisterWithPrice("System.Blockchain.GetTransactionHeight", self.Blockchain_GetTransactionHeight, 100)
        self.RegisterWithPrice("System.Blockchain.GetContract", self.Blockchain_GetContract, 100)
        self.RegisterWithPrice("System.Header.GetIndex", self.Header_GetIndex, 1)
        self.RegisterWithPrice("System.Header.GetHash", self.Header_GetHash, 1)
        self.RegisterWithPrice("System.Header.GetPrevHash", self.Header_GetPrevHash, 1)
        self.RegisterWithPrice("System.Header.GetTimestamp", self.Header_GetTimestamp, 1)
        self.RegisterWithPrice("System.Block.GetTransactionCount", self.Block_GetTransactionCount, 1)
        self.RegisterWithPrice("System.Block.GetTransactions", self.Block_GetTransactions, 1)
        self.RegisterWithPrice("System.Block.GetTransaction", self.Block_GetTransaction, 1)
        self.RegisterWithPrice("System.Transaction.GetHash", self.Transaction_GetHash, 1)
        self.RegisterWithPrice("System.Storage.GetContext", self.Storage_GetContext, 1)
        self.RegisterWithPrice("System.Storage.GetReadOnlyContext", self.Storage_GetReadOnlyContext, 1)
        self.RegisterWithPrice("System.Storage.Get", self.Storage_Get, 100)
        self.Register("System.Storage.Put", self.Storage_Put)
        self.Register("System.Storage.PutEx", self.Storage_PutEx)
        self.RegisterWithPrice("System.Storage.Delete", self.Storage_Delete, 100)
        self.RegisterWithPrice("System.StorageContext.AsReadOnly", self.StorageContext_AsReadOnly, 1)

    def CheckStorageContext(self, context):
        if context is None:
            return False

        if type(context) != neo.SmartContract.StorageContext.StorageContext:
            return False

        contract = self.Snapshot.Contracts.TryGet(context.ScriptHash.ToBytes())

        if contract is not None:
            if contract.HasStorage:
                return True

        return False

    def GetPrice(self, hash: int):
        return self.prices.get(hash, 0)

    def ExecutionCompleted(self, engine, success, error=None):
        height = GetBlockchain().Height + 1
        tx_hash = None

        if engine.ScriptContainer:
            tx_hash = engine.ScriptContainer.Hash

        if not tx_hash:
            tx_hash = UInt256(data=bytearray(32))

        entry_script = None
        try:
            # get the first script that was executed
            # this is usually the script that sets up the script to be executed
            entry_script = UInt160(data=engine.ExecutedScriptHashes[0])

            # ExecutedScriptHashes[1] will usually be the first contract executed
            if len(engine.ExecutedScriptHashes) > 1:
                entry_script = UInt160(data=engine.ExecutedScriptHashes[1])
        except Exception as e:
            logger.error("Could not get entry script: %s " % e)

        payload = ContractParameter(ContractParameterType.Array, value=[])
        for item in engine.ResultStack.Items:
            payload.Value.append(ContractParameter.ToParameter(item))

        if success:

            # dispatch all notify events, along with the success of the contract execution
            for notify_event_args in self.notifications:
                self.events_to_dispatch.append(NotifyEvent(SmartContractEvent.RUNTIME_NOTIFY, notify_event_args.State,
                                                           notify_event_args.ScriptHash, height, tx_hash,
                                                           success, engine.testMode))

            if self.Trigger == TriggerType.Application:
                self.events_to_dispatch.append(SmartContractEvent(SmartContractEvent.EXECUTION_SUCCESS, payload, entry_script,
                                                                  height, tx_hash, success, engine.testMode))
            else:
                self.events_to_dispatch.append(SmartContractEvent(SmartContractEvent.VERIFICATION_SUCCESS, payload, entry_script,
                                                                  height, tx_hash, success, engine.testMode))

        else:
            # when a contract exits in a faulted state
            # we should display that in the notification
            if not error:
                error = 'Execution exited in a faulted state. Any payload besides this message contained in this event is the contents of the EvaluationStack of the current script context.'

            payload.Value.append(ContractParameter(ContractParameterType.String, error))

            # If we do not add the eval stack, then exceptions that are raised in a contract
            # are not displayed to the event consumer
            if engine._InvocationStack.Count > 1:
                [payload.Value.append(ContractParameter.ToParameter(item)) for item in engine.CurrentContext.EvaluationStack.Items]

            if self.Trigger == TriggerType.Application:
                self.events_to_dispatch.append(
                    SmartContractEvent(SmartContractEvent.EXECUTION_FAIL, payload,
                                       entry_script, height, tx_hash, success, engine.testMode))
            else:
                self.events_to_dispatch.append(
                    SmartContractEvent(SmartContractEvent.VERIFICATION_FAIL, payload,
                                       entry_script, height, tx_hash, success, engine.testMode))

        self.notifications = []

    def Runtime_Platform(self, engine):
        engine.CurrentContext.EvaluationStack.PushT(b'\x4e\x45\x4f')  # NEO
        return True

    def Runtime_GetTrigger(self, engine):

        engine.CurrentContext.EvaluationStack.PushT(int.from_bytes(self.Trigger, 'little'))

        return True

    def CheckWitnessHash(self, engine, hash):
        if not engine.ScriptContainer:
            return False

        if self._hashes_for_verifying is None:
            container = engine.ScriptContainer
            self._hashes_for_verifying = container.GetScriptHashesForVerifying(self.Snapshot)

        return True if hash in self._hashes_for_verifying else False

    def CheckWitnessPubkey(self, engine, pubkey):
        scripthash = Contract.CreateSignatureRedeemScript(pubkey)
        return self.CheckWitnessHash(engine, Crypto.ToScriptHash(scripthash))

    def Runtime_CheckWitness(self, engine: ExecutionEngine):
        hashOrPubkey = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()

        result = False

        if len(hashOrPubkey) == 20:
            result = self.CheckWitnessHash(engine, UInt160(data=hashOrPubkey))

        elif len(hashOrPubkey) == 33:
            try:
                point = ECDSA.decode_secp256r1(hashOrPubkey, unhex=False).G
            except ValueError:
                return False
            result = self.CheckWitnessPubkey(engine, point)
        else:
            return False

        engine.CurrentContext.EvaluationStack.PushT(result)

        return True

    def Runtime_Notify(self, engine: ExecutionEngine):
        state = engine.CurrentContext.EvaluationStack.Pop()

        payload = ContractParameter.ToParameter(state)

        args = NotifyEventArgs(
            engine.ScriptContainer,
            UInt160(data=engine.CurrentContext.ScriptHash()),
            payload
        )

        self.notifications.append(args)

        if settings.emit_notify_events_on_sc_execution_error:
            # emit Notify events even if the SC execution might fail.
            tx_hash = engine.ScriptContainer.Hash
            height = GetBlockchain().Height + 1
            success = None
            self.events_to_dispatch.append(NotifyEvent(SmartContractEvent.RUNTIME_NOTIFY, payload,
                                                       args.ScriptHash, height, tx_hash,
                                                       success, engine.testMode))

        return True

    def Runtime_Log(self, engine: ExecutionEngine):
        item = engine.CurrentContext.EvaluationStack.Pop()
        # will raise an exception for types that don't support it
        item.GetByteArray()

        # if we pass we can call the convenience method to pretty print the data
        message = item.GetString()

        hash = UInt160(data=engine.CurrentContext.ScriptHash())

        tx_hash = None

        if engine.ScriptContainer:
            tx_hash = engine.ScriptContainer.Hash
        engine.write_log(str(message))

        # Build and emit smart contract event
        self.events_to_dispatch.append(SmartContractEvent(SmartContractEvent.RUNTIME_LOG,
                                                          ContractParameter(ContractParameterType.String, value=message),
                                                          hash,
                                                          GetBlockchain().Height + 1,
                                                          tx_hash,
                                                          test_mode=engine.testMode))

        return True

    def Runtime_GetCurrentTime(self, engine: ExecutionEngine):
        if self.Snapshot.PersistingBlock is None:
            BC = GetBlockchain()
            header = BC.GetHeaderByHeight(BC.Height)
            engine.CurrentContext.EvaluationStack.PushT(header.Timestamp + GetBlockchain().SECONDS_PER_BLOCK)
        else:
            engine.CurrentContext.EvaluationStack.PushT(self.Snapshot.PersistingBlock.Timestamp)
        return True

    def Runtime_Serialize(self, engine: ExecutionEngine):
        stack_item = engine.CurrentContext.EvaluationStack.Pop()

        ms = StreamManager.GetStream()
        writer = BinaryWriter(ms)
        try:
            stack_item.Serialize(writer)
        except Exception as e:
            StreamManager.ReleaseStream(ms)
            return False

        ms.flush()

        if ms.tell() > engine.maxItemSize:
            StreamManager.ReleaseStream(ms)
            return False

        retVal = ByteArray(ms.getvalue())
        StreamManager.ReleaseStream(ms)
        engine.CurrentContext.EvaluationStack.PushT(retVal)

        return True

    def Runtime_Deserialize(self, engine: ExecutionEngine):
        data = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()

        ms = StreamManager.GetStream(data=data)
        reader = BinaryReader(ms)
        try:
            stack_item = StackItem.DeserializeStackItem(reader)
            engine.CurrentContext.EvaluationStack.PushT(stack_item)
        except ValueError as e:
            # can't deserialize type
            return False
        finally:
            StreamManager.ReleaseStream(ms)
        return True

    def Blockchain_GetHeight(self, engine: ExecutionEngine):
        if GetBlockchain() is None:
            engine.CurrentContext.EvaluationStack.PushT(0)
        else:
            engine.CurrentContext.EvaluationStack.PushT(GetBlockchain().Height)

        return True

    def Blockchain_GetHeader(self, engine: ExecutionEngine):
        data = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()

        header = None

        if len(data) <= 5:

            height = BigInteger.FromBytes(data)

            if GetBlockchain() is not None:

                header = GetBlockchain().GetHeaderBy(height_or_hash=height)

            elif height == 0:

                header = GetBlockchain().GenesisBlock().Header

        elif len(data) == 32:

            hash = UInt256(data=data)

            if GetBlockchain() is not None:

                header = GetBlockchain().GetHeaderBy(height_or_hash=hash)

            elif hash == GetBlockchain().GenesisBlock().Hash:

                header = GetBlockchain().GenesisBlock().Header

        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(header))
        return True

    def Blockchain_GetBlock(self, engine: ExecutionEngine):
        data = engine.CurrentContext.EvaluationStack.Pop()

        if data:
            data = data.GetByteArray()
        else:
            return False

        block = None

        if len(data) <= 5:
            height = BigInteger.FromBytes(data)

            if GetBlockchain() is not None:

                block = GetBlockchain().GetBlockByHeight(height)

            elif height == 0:

                block = GetBlockchain().GenesisBlock()

        elif len(data) == 32:

            hash = UInt256(data=data).ToBytes()

            if GetBlockchain() is not None:

                block = GetBlockchain().GetBlockByHash(hash=hash)

            elif hash == GetBlockchain().GenesisBlock().Hash:

                block = GetBlockchain().GenesisBlock().Header

        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(block))
        return True

    def Blockchain_GetTransaction(self, engine: ExecutionEngine):
        data = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()
        tx = None

        if GetBlockchain() is not None:
            tx, height = GetBlockchain().GetTransaction(UInt256(data=data))

        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(tx))
        return True

    def Blockchain_GetTransactionHeight(self, engine: ExecutionEngine):
        data = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()
        height = -1

        if GetBlockchain() is not None:
            tx, height = GetBlockchain().GetTransaction(UInt256(data=data))

        engine.CurrentContext.EvaluationStack.PushT(height)
        return True

    def Blockchain_GetContract(self, engine: ExecutionEngine):
        hash = UInt160(data=engine.CurrentContext.EvaluationStack.Pop().GetByteArray())
        contract = self.Snapshot.Contracts.TryGet(hash.ToBytes())
        if contract is None:
            engine.CurrentContext.EvaluationStack.PushT(bytearray(0))
        else:
            engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(contract))
        return True

    def Header_GetIndex(self, engine: ExecutionEngine):
        header = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.Core.BlockBase.BlockBase)
        if header is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(header.Index)
        return True

    def Header_GetHash(self, engine: ExecutionEngine):
        header = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.Core.BlockBase.BlockBase)
        if header is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(header.Hash.ToArray())
        return True

    def Header_GetPrevHash(self, engine: ExecutionEngine):
        header = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.Core.BlockBase.BlockBase)
        if header is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(header.PrevHash.ToArray())
        return True

    def Header_GetTimestamp(self, engine: ExecutionEngine):
        header = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.Core.BlockBase.BlockBase)
        if header is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(header.Timestamp)

        return True

    def Block_GetTransactionCount(self, engine: ExecutionEngine):
        block = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.Core.Block.Block)
        if block is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(len(block.Transactions))
        return True

    def Block_GetTransactions(self, engine: ExecutionEngine):
        block = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.Core.Block.Block)
        if block is None:
            return False

        if len(block.FullTransactions) > engine.maxArraySize:
            return False

        txlist = [StackItem.FromInterface(tx) for tx in block.FullTransactions]
        engine.CurrentContext.EvaluationStack.PushT(txlist)
        return True

    def Block_GetTransaction(self, engine: ExecutionEngine):
        block = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.Core.Block.Block)
        index = engine.CurrentContext.EvaluationStack.Pop().GetBigInteger()

        if block is None or index < 0 or index > len(block.Transactions):
            return False

        tx = StackItem.FromInterface(block.FullTransactions[index])
        engine.CurrentContext.EvaluationStack.PushT(tx)
        return True

    def Transaction_GetHash(self, engine: ExecutionEngine):
        tx = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.Core.TX.Transaction.Transaction)
        if tx is None:
            return False

        engine.CurrentContext.EvaluationStack.PushT(tx.Hash.ToArray())
        return True

    def Storage_GetContext(self, engine: ExecutionEngine):
        hash = UInt160(data=engine.CurrentContext.ScriptHash())
        context = neo.SmartContract.StorageContext.StorageContext(script_hash=hash)

        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(context))

        return True

    def Storage_GetReadOnlyContext(self, engine: ExecutionEngine):
        hash = UInt160(data=engine.CurrentContext.ScriptHash())
        context = neo.SmartContract.StorageContext.StorageContext(script_hash=hash, read_only=True)

        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(context))

        return True

    def StorageContext_AsReadOnly(self, engine: ExecutionEngine):
        context = engine.CurrentContext.EvaluationStack.Pop.GetInterface(neo.SmartContract.StorageContext.StorageContext)

        if context is None:
            return False

        if not context.IsReadOnly:
            context = neo.SmartContract.StorageContext.StorageContext(script_hash=context.ScriptHash, read_only=True)

        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(context))
        return True

    def Storage_Get(self, engine: ExecutionEngine):
        context = None
        try:
            item = engine.CurrentContext.EvaluationStack.Pop()
            context = item.GetInterface(neo.SmartContract.StorageContext.StorageContext)
        except Exception as e:
            return False

        if not self.CheckStorageContext(context):
            return False

        key = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()
        storage_key = StorageKey(script_hash=context.ScriptHash, key=key)
        item = self.Snapshot.Storages.TryGet(storage_key.ToArray())

        keystr = key

        valStr = bytearray(0)

        if item is not None:
            valStr = bytearray(item.Value)

        if item is not None:
            engine.CurrentContext.EvaluationStack.PushT(bytearray(item.Value))

        else:
            engine.CurrentContext.EvaluationStack.PushT(bytearray(0))

        tx_hash = None
        if engine.ScriptContainer:
            tx_hash = engine.ScriptContainer.Hash

        self.events_to_dispatch.append(
            SmartContractEvent(SmartContractEvent.STORAGE_GET, ContractParameter(ContractParameterType.String, value='%s -> %s' % (keystr, valStr)),
                               context.ScriptHash, GetBlockchain().Height + 1, tx_hash, test_mode=engine.testMode))

        return True

    def Storage_Put(self, engine: ExecutionEngine):

        context = None
        try:
            context = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.SmartContract.StorageContext.StorageContext)
        except Exception as e:
            return False

        if not self.CheckStorageContext(context):
            return False

        key = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()
        if len(key) > 1024:
            return False

        value = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()

        storage_key = StorageKey(script_hash=context.ScriptHash, key=key)
        item = self.Snapshot.Storages.GetAndChange(storage_key.ToArray(), lambda: StorageItem())
        item.Value = value

        keystr = key
        valStr = bytearray(item.Value)

        if type(engine) == ExecutionEngine:
            test_mode = False
        else:
            test_mode = engine.testMode

        self.events_to_dispatch.append(
            SmartContractEvent(SmartContractEvent.STORAGE_PUT, ContractParameter(ContractParameterType.String, '%s -> %s' % (keystr, valStr)),
                               context.ScriptHash, GetBlockchain().Height + 1,
                               engine.ScriptContainer.Hash if engine.ScriptContainer else None,
                               test_mode=test_mode))

        return True

    def Contract_GetStorageContext(self, engine):

        contract = engine.CurrentContext.EvaluationStack.Pop().GetInterface(ContractState)

        shash = contract.Code.ScriptHash()

        if shash.ToBytes() in self._contracts_created:

            created = self._contracts_created[shash.ToBytes()]

            if created == UInt160(data=engine.CurrentContext.ScriptHash()):
                context = neo.SmartContract.StorageContext.StorageContext(script_hash=shash)
                engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(context))

                return True

        return False

    def Contract_Destroy(self, engine):
        hash = UInt160(data=engine.CurrentContext.ScriptHash())

        contract = self.Snapshot.Contracts.TryGet(hash.ToBytes())

        if contract is not None:

            self.Snapshot.Contracts.Delete(hash.ToBytes())

            if contract.HasStorage:

                to_del = []
                for k, v in self.Snapshot.Storages.Find(hash.ToArray()):
                    storage_key = StorageKey(script_hash=hash, key=k[20:])
                    # Snapshot.Storages.Delete() modifies the underlying dictionary of the cache we'd be iterating
                    # over using Storages.Find. We therefore need to postpone deletion
                    to_del.append(storage_key)

                for storage_key in to_del:
                    self.Snapshot.Storages.Delete(storage_key.ToArray())

        self.events_to_dispatch.append(
            SmartContractEvent(SmartContractEvent.CONTRACT_DESTROY, ContractParameter(ContractParameterType.InteropInterface, contract),
                               hash, GetBlockchain().Height + 1,
                               engine.ScriptContainer.Hash if engine.ScriptContainer else None,
                               test_mode=engine.testMode))
        return True

    def Storage_PutEx(self, engine):
        logger.error("Storage_PutEx not implemented!")
        return False

    def Storage_Delete(self, engine: ExecutionEngine):
        if self.Trigger != TriggerType.Application and self.Trigger != TriggerType.ApplicationR:
            return False

        context = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.SmartContract.StorageContext.StorageContext)
        if not self.CheckStorageContext(context):
            return False
        if context.IsReadOnly:
            return False

        key = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()
        storage_key = StorageKey(script_hash=context.ScriptHash, key=key)

        if type(engine) == ExecutionEngine:
            test_mode = False
        else:
            test_mode = engine.testMode
        self.events_to_dispatch.append(SmartContractEvent(SmartContractEvent.STORAGE_DELETE, ContractParameter(ContractParameterType.String, key),
                                                          context.ScriptHash, GetBlockchain().Height + 1,
                                                          engine.ScriptContainer.Hash if engine.ScriptContainer else None,
                                                          test_mode=test_mode))

        item = self.Snapshot.Storages.TryGet(storage_key.ToArray())
        if item and item.IsConstant:
            return False

        self.Snapshot.Storages.Delete(storage_key.ToArray())

        return True
