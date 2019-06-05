from neo.VM.InteropService import InteropService
from neo.SmartContract.Contract import Contract
from neo.SmartContract.NotifyEventArgs import NotifyEventArgs
from neo.SmartContract.StorageContext import StorageContext
from neo.Core.State.StorageKey import StorageKey
from neo.Core.Blockchain import Blockchain
from neo.Core.Cryptography.Crypto import Crypto
from neo.Core.BigInteger import BigInteger
from neo.Core.UInt160 import UInt160
from neo.Core.UInt256 import UInt256
from neo.SmartContract.SmartContractEvent import SmartContractEvent, NotifyEvent
from neo.SmartContract.ContractParameter import ContractParameter, ContractParameterType
from neo.Core.Cryptography.ECCurve import ECDSA
from neo.SmartContract.TriggerType import Application, Verification
from neo.VM.InteropService import StackItem, ByteArray, Array, Map
from neo.VM.ExecutionEngine import ExecutionEngine
from neo.Settings import settings
from neo.Core.IO.BinaryReader import BinaryReader
from neo.Core.IO.BinaryWriter import BinaryWriter
from neo.IO.MemoryStream import StreamManager
from neo.Implementations.Blockchains.LevelDB.DBPrefix import DBPrefix
from neo.Core.State.ContractState import ContractState
from neo.Core.State.AccountState import AccountState
from neo.Core.State.AssetState import AssetState
from neo.Core.State.StorageItem import StorageItem
from neo.logging import log_manager

logger = log_manager.getLogger('vm')


class StateReader(InteropService):

    @property
    def Accounts(self):
        if not self._accounts:
            self._accounts = Blockchain.Default().GetStates(DBPrefix.ST_Account, AccountState)
        return self._accounts

    @property
    def Assets(self):
        if not self._assets:
            self._assets = Blockchain.Default().GetStates(DBPrefix.ST_Asset, AssetState)
        return self._assets

    @property
    def Contracts(self):
        if not self._contracts:
            self._contracts = Blockchain.Default().GetStates(DBPrefix.ST_Contract, ContractState)
        return self._contracts

    @property
    def Storages(self):
        if not self._storages:
            self._storages = Blockchain.Default().GetStates(DBPrefix.ST_Storage, StorageItem)
        return self._storages

    def RegisterWithPrice(self, method, func, price):
        self._dictionary[method] = func
        self.prices.update({hash(method): price})

    def __init__(self):

        super(StateReader, self).__init__()

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

        if type(context) != StorageContext:
            return False

        contract = self.Contracts.TryGet(context.ScriptHash.ToBytes())

        if contract is not None:
            if contract.HasStorage:
                return True

        return False

    def GetPrice(self, hash: int):
        return self.prices.get(hash, 0)

    def ExecutionCompleted(self, engine, success, error=None):
        height = Blockchain.Default().Height + 1
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

            if engine.Trigger == Application:
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

            if engine.Trigger == Application:
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

        engine.CurrentContext.EvaluationStack.PushT(int.from_bytes(engine.Trigger, 'little'))

        return True

    def CheckWitnessHash(self, engine, hash):
        if not engine.ScriptContainer:
            return False

        if self._hashes_for_verifying is None:
            container = engine.ScriptContainer
            self._hashes_for_verifying = container.GetScriptHashesForVerifying()

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
            height = Blockchain.Default().Height + 1
            success = None
            self.events_to_dispatch.append(NotifyEvent(SmartContractEvent.RUNTIME_NOTIFY, payload,
                                                       args.ScriptHash, height, tx_hash,
                                                       success, engine.testMode))

        return True

    def Runtime_Log(self, engine: ExecutionEngine):
        message = engine.CurrentContext.EvaluationStack.Pop().GetString()

        hash = UInt160(data=engine.CurrentContext.ScriptHash())

        tx_hash = None

        if engine.ScriptContainer:
            tx_hash = engine.ScriptContainer.Hash
        engine.write_log(str(message))

        # Build and emit smart contract event
        self.events_to_dispatch.append(SmartContractEvent(SmartContractEvent.RUNTIME_LOG,
                                                          ContractParameter(ContractParameterType.String, value=message),
                                                          hash,
                                                          Blockchain.Default().Height + 1,
                                                          tx_hash,
                                                          test_mode=engine.testMode))

        return True

    def Runtime_GetCurrentTime(self, engine: ExecutionEngine):
        BC = Blockchain.Default()
        header = BC.GetHeaderByHeight(BC.Height)
        if header is None:
            header = Blockchain.GenesisBlock()

        engine.CurrentContext.EvaluationStack.PushT(header.Timestamp + Blockchain.SECONDS_PER_BLOCK)
        return True

    def Runtime_Serialize(self, engine: ExecutionEngine):
        stack_item = engine.CurrentContext.EvaluationStack.Pop()

        ms = StreamManager.GetStream()
        writer = BinaryWriter(ms)
        try:
            stack_item.Serialize(writer)
        except Exception as e:
            StreamManager.ReleaseStream(ms)
            logger.error("Cannot serialize item %s: %s " % (stack_item, e))
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
            logger.error("%s " % e)
            return False
        finally:
            StreamManager.ReleaseStream(ms)
        return True

    def Blockchain_GetHeight(self, engine: ExecutionEngine):
        if Blockchain.Default() is None:
            engine.CurrentContext.EvaluationStack.PushT(0)
        else:
            engine.CurrentContext.EvaluationStack.PushT(Blockchain.Default().Height)

        return True

    def Blockchain_GetHeader(self, engine: ExecutionEngine):
        data = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()

        header = None

        if len(data) <= 5:

            height = BigInteger.FromBytes(data)

            if Blockchain.Default() is not None:

                header = Blockchain.Default().GetHeaderBy(height_or_hash=height)

            elif height == 0:

                header = Blockchain.GenesisBlock().Header

        elif len(data) == 32:

            hash = UInt256(data=data)

            if Blockchain.Default() is not None:

                header = Blockchain.Default().GetHeaderBy(height_or_hash=hash)

            elif hash == Blockchain.GenesisBlock().Hash:

                header = Blockchain.GenesisBlock().Header

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

            if Blockchain.Default() is not None:

                block = Blockchain.Default().GetBlockByHeight(height)

            elif height == 0:

                block = Blockchain.GenesisBlock()

        elif len(data) == 32:

            hash = UInt256(data=data).ToBytes()

            if Blockchain.Default() is not None:

                block = Blockchain.Default().GetBlockByHash(hash=hash)

            elif hash == Blockchain.GenesisBlock().Hash:

                block = Blockchain.GenesisBlock().Header

        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(block))
        return True

    def Blockchain_GetTransaction(self, engine: ExecutionEngine):
        data = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()
        tx = None

        if Blockchain.Default() is not None:
            tx, height = Blockchain.Default().GetTransaction(UInt256(data=data))

        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(tx))
        return True

    def Blockchain_GetTransactionHeight(self, engine: ExecutionEngine):
        data = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()
        height = -1

        if Blockchain.Default() is not None:
            tx, height = Blockchain.Default().GetTransaction(UInt256(data=data))

        engine.CurrentContext.EvaluationStack.PushT(height)
        return True

    def Blockchain_GetContract(self, engine: ExecutionEngine):
        hash = UInt160(data=engine.CurrentContext.EvaluationStack.Pop().GetByteArray())
        contract = self.Contracts.TryGet(hash.ToBytes())
        if contract is None:
            engine.CurrentContext.EvaluationStack.PushT(bytearray(0))
        else:
            engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(contract))
        return True

    def Header_GetIndex(self, engine: ExecutionEngine):
        header = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if header is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(header.Index)
        return True

    def Header_GetHash(self, engine: ExecutionEngine):
        header = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if header is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(header.Hash.ToArray())
        return True

    def Header_GetPrevHash(self, engine: ExecutionEngine):
        header = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if header is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(header.PrevHash.ToArray())
        return True

    def Header_GetTimestamp(self, engine: ExecutionEngine):
        header = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if header is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(header.Timestamp)

        return True

    def Block_GetTransactionCount(self, engine: ExecutionEngine):
        block = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if block is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(len(block.Transactions))
        return True

    def Block_GetTransactions(self, engine: ExecutionEngine):
        block = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if block is None:
            return False

        if len(block.FullTransactions) > engine.maxArraySize:
            return False

        txlist = [StackItem.FromInterface(tx) for tx in block.FullTransactions]
        engine.CurrentContext.EvaluationStack.PushT(txlist)
        return True

    def Block_GetTransaction(self, engine: ExecutionEngine):
        block = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        index = engine.CurrentContext.EvaluationStack.Pop().GetBigInteger()

        if block is None or index < 0 or index > len(block.Transactions):
            return False

        tx = StackItem.FromInterface(block.FullTransactions[index])
        engine.CurrentContext.EvaluationStack.PushT(tx)
        return True

    def Transaction_GetHash(self, engine: ExecutionEngine):
        tx = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if tx is None:
            return False

        engine.CurrentContext.EvaluationStack.PushT(tx.Hash.ToArray())
        return True

    def Storage_GetContext(self, engine: ExecutionEngine):
        hash = UInt160(data=engine.CurrentContext.ScriptHash())
        context = StorageContext(script_hash=hash)

        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(context))

        return True

    def Storage_GetReadOnlyContext(self, engine: ExecutionEngine):
        hash = UInt160(data=engine.CurrentContext.ScriptHash())
        context = StorageContext(script_hash=hash, read_only=True)

        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(context))

        return True

    def StorageContext_AsReadOnly(self, engine: ExecutionEngine):
        context = engine.CurrentContext.EvaluationStack.Pop.GetInterface()

        if context is None:
            return False

        if not context.IsReadOnly:
            context = StorageContext(script_hash=context.ScriptHash, read_only=True)

        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(context))
        return True

    def Storage_Get(self, engine: ExecutionEngine):
        context = None
        try:
            item = engine.CurrentContext.EvaluationStack.Pop()
            context = item.GetInterface()
        except Exception as e:
            logger.error("could not get storage context %s " % e)
            return False

        if not self.CheckStorageContext(context):
            return False

        key = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()
        storage_key = StorageKey(script_hash=context.ScriptHash, key=key)
        item = self.Storages.TryGet(storage_key.ToArray())

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
                               context.ScriptHash, Blockchain.Default().Height + 1, tx_hash, test_mode=engine.testMode))

        return True

    def Storage_Put(self, engine: ExecutionEngine):

        context = None
        try:
            context = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        except Exception as e:
            logger.error("Storage Context Not found on stack")
            return False

        if not self.CheckStorageContext(context):
            return False

        key = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()
        if len(key) > 1024:
            return False

        value = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()

        new_item = StorageItem(value=value)
        storage_key = StorageKey(script_hash=context.ScriptHash, key=key)
        item = self._storages.ReplaceOrAdd(storage_key.ToArray(), new_item)

        keystr = key
        valStr = bytearray(item.Value)

        if type(engine) == ExecutionEngine:
            test_mode = False
        else:
            test_mode = engine.testMode

        self.events_to_dispatch.append(
            SmartContractEvent(SmartContractEvent.STORAGE_PUT, ContractParameter(ContractParameterType.String, '%s -> %s' % (keystr, valStr)),
                               context.ScriptHash, Blockchain.Default().Height + 1,
                               engine.ScriptContainer.Hash if engine.ScriptContainer else None,
                               test_mode=test_mode))

        return True

    def Contract_GetStorageContext(self, engine):

        contract = engine.CurrentContext.EvaluationStack.Pop().GetInterface()

        shash = contract.Code.ScriptHash()

        if shash.ToBytes() in self._contracts_created:

            created = self._contracts_created[shash.ToBytes()]

            if created == UInt160(data=engine.CurrentContext.ScriptHash()):
                context = StorageContext(script_hash=shash)
                engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(context))

                return True

        return False

    def Contract_Destroy(self, engine):
        hash = UInt160(data=engine.CurrentContext.ScriptHash())

        contract = self._contracts.TryGet(hash.ToBytes())

        if contract is not None:

            self._contracts.Remove(hash.ToBytes())

            if contract.HasStorage:

                for pair in self._storages.Find(hash.ToBytes()):
                    self._storages.Remove(pair.Key)

        self.events_to_dispatch.append(
            SmartContractEvent(SmartContractEvent.CONTRACT_DESTROY, ContractParameter(ContractParameterType.InteropInterface, contract),
                               hash, Blockchain.Default().Height + 1,
                               engine.ScriptContainer.Hash if engine.ScriptContainer else None,
                               test_mode=engine.testMode))
        return True

    def Storage_PutEx(self, engine):
        logger.error("Storage_PutEx not implemented!")
        return False

    def Storage_Delete(self, engine: ExecutionEngine):

        context = engine.CurrentContext.EvaluationStack.Pop().GetInterface()

        if not self.CheckStorageContext(context):
            return False

        key = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()

        storage_key = StorageKey(script_hash=context.ScriptHash, key=key)

        keystr = key
        if len(key) == 20:
            keystr = Crypto.ToAddress(UInt160(data=key))

        if type(engine) == ExecutionEngine:
            test_mode = False
        else:
            test_mode = engine.testMode
        self.events_to_dispatch.append(SmartContractEvent(SmartContractEvent.STORAGE_DELETE, ContractParameter(ContractParameterType.String, keystr),
                                                          context.ScriptHash, Blockchain.Default().Height + 1,
                                                          engine.ScriptContainer.Hash if engine.ScriptContainer else None,
                                                          test_mode=test_mode))

        self._storages.Remove(storage_key.ToArray())

        return True
