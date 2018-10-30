import sys
from neo.Core.State.ContractState import ContractState
from neo.Core.State.AssetState import AssetState
from neo.Core.Blockchain import Blockchain
from neo.Core.FunctionCode import FunctionCode
from neo.Core.State.StorageItem import StorageItem
from neo.Core.State.StorageKey import StorageKey
from neo.Core.State.ValidatorState import ValidatorState
from neo.Core.AssetType import AssetType
from neocore.Cryptography.Crypto import Crypto
from neocore.Cryptography.ECCurve import ECDSA
from neocore.UInt160 import UInt160
from neocore.UInt256 import UInt256
from neocore.Fixed8 import Fixed8
from neo.VM.InteropService import StackItem
from neo.VM.ExecutionEngine import ExecutionEngine
from neo.SmartContract.StorageContext import StorageContext
from neo.SmartContract.StateReader import StateReader
from neo.SmartContract.ContractParameter import ContractParameter, ContractParameterType
from neo.EventHub import SmartContractEvent
from neo.logging import log_manager

logger = log_manager.getLogger('vm')


class StateMachine(StateReader):
    _validators = None
    _wb = None

    _contracts_created = {}

    def __init__(self, accounts, validators, assets, contracts, storages, wb):

        super(StateMachine, self).__init__()

        self._accounts = accounts
        self._validators = validators
        self._assets = assets
        self._contracts = contracts
        self._storages = storages
        self._wb = wb

        self._accounts.MarkForReset()
        self._validators.MarkForReset()
        self._assets.MarkForReset()
        self._contracts.MarkForReset()
        self._storages.MarkForReset()

        # Standard Library
        self.Register("System.Contract.GetStorageContext", self.Contract_GetStorageContext)
        self.Register("System.Contract.Destroy", self.Contract_Destroy)
        self.Register("System.Storage.Put", self.Storage_Put)
        self.Register("System.Storage.Delete", self.Storage_Delete)

        # Neo specific
        self.Register("Neo.Asset.Create", self.Asset_Create)
        self.Register("Neo.Asset.Renew", self.Asset_Renew)
        self.Register("Neo.Contract.Migrate", self.Contract_Migrate)
        self.Register("Neo.Contract.Create", self.Contract_Create)

        # Old
        self.Register("Neo.Contract.GetStorageContext", self.Contract_GetStorageContext)
        self.Register("Neo.Contract.Destroy", self.Contract_Destroy)
        self.Register("Neo.Storage.Put", self.Storage_Put)
        self.Register("Neo.Storage.Delete", self.Storage_Delete)

        # Very old
        self.Register("AntShares.Account.SetVotes", self.Deprecated_Method)
        self.Register("AntShares.Asset.Create", self.Asset_Create)
        self.Register("AntShares.Asset.Renew", self.Asset_Renew)
        self.Register("AntShares.Contract.Create", self.Contract_Create)
        self.Register("AntShares.Contract.Migrate", self.Contract_Migrate)
        self.Register("AntShares.Contract.GetStorageContext", self.Contract_GetStorageContext)
        self.Register("AntShares.Contract.Destroy", self.Contract_Destroy)
        self.Register("AntShares.Storage.Put", self.Storage_Put)
        self.Register("AntShares.Storage.Delete", self.Storage_Delete)

    def ExecutionCompleted(self, engine, success, error=None):

        # commit storages right away
        if success:
            self.Commit()
        else:
            self.ResetState()

        super(StateMachine, self).ExecutionCompleted(engine, success, error)

    def Commit(self):
        if self._wb is not None:
            self._accounts.Commit(self._wb, False)
            self._validators.Commit(self._wb, False)
            self._assets.Commit(self._wb, False)
            self._contracts.Commit(self._wb, False)
            self._storages.Commit(self._wb, False)

    def ResetState(self):
        self._accounts.Reset()
        self._validators.Reset()
        self._assets.Reset()
        self._contracts.Reset()
        self._storages.Reset()

    def TestCommit(self):
        if self._storages.DebugStorage:
            self._storages.Commit(self._wb, False)

    def Deprecated_Method(self, engine):
        logger.debug("Method No Longer operational")

    def Asset_Create(self, engine: ExecutionEngine):

        tx = engine.ScriptContainer

        asset_type = int(engine.CurrentContext.EvaluationStack.Pop().GetBigInteger())

        if asset_type not in AssetType.AllTypes() or \
                asset_type == AssetType.CreditFlag or \
                asset_type == AssetType.DutyFlag or \
                asset_type == AssetType.GoverningToken or \
                asset_type == AssetType.UtilityToken:
            return False

        if len(engine.CurrentContext.EvaluationStack.Peek().GetByteArray()) > 1024:
            return False

        name = engine.CurrentContext.EvaluationStack.Pop().GetByteArray().decode('utf-8')

        amount = Fixed8(engine.CurrentContext.EvaluationStack.Pop().GetBigInteger())

        if amount == Fixed8.Zero() or amount < Fixed8.NegativeSatoshi():
            return False

        if asset_type == AssetType.Invoice and amount != Fixed8.NegativeSatoshi():
            return False

        precision = int(engine.CurrentContext.EvaluationStack.Pop().GetBigInteger())

        if precision > 8:
            return False

        if asset_type == AssetType.Share and precision != 0:
            return False

        if amount != Fixed8.NegativeSatoshi() and amount.value % pow(10, 8 - precision) != 0:
            return False

        ownerData = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()

        owner = ECDSA.decode_secp256r1(ownerData, unhex=False).G

        if owner.IsInfinity:
            return False

        if not self.CheckWitnessPubkey(engine, owner):
            logger.error("check witness false...")
            return False

        admin = UInt160(data=engine.CurrentContext.EvaluationStack.Pop().GetByteArray())

        issuer = UInt160(data=engine.CurrentContext.EvaluationStack.Pop().GetByteArray())

        new_asset = AssetState(
            asset_id=tx.Hash, asset_type=asset_type, name=name, amount=amount,
            available=Fixed8.Zero(), precision=precision, fee_mode=0, fee=Fixed8.Zero(),
            fee_addr=UInt160(), owner=owner, admin=admin, issuer=issuer,
            expiration=Blockchain.Default().Height + 1 + 2000000, is_frozen=False
        )

        asset = self._assets.ReplaceOrAdd(tx.Hash.ToBytes(), new_asset)

        # print("*****************************************************")
        # print("CREATED ASSET %s " % tx.Hash.ToBytes())
        # print("*****************************************************")
        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(asset))

        return True

    def Asset_Renew(self, engine: ExecutionEngine):

        current_asset = engine.CurrentContext.EvaluationStack.Pop().GetInterface()

        if current_asset is None:
            return False

        years = engine.CurrentContext.EvaluationStack.Pop().GetBigInteger()

        asset = self._assets.GetAndChange(current_asset.AssetId.ToBytes())

        if asset.Expiration < Blockchain.Default().Height + 1:
            asset.Expiration = Blockchain.Default().Height + 1

        try:

            asset.Expiration = asset.Expiration + years * 2000000

        except Exception as e:
            logger.error("could not set expiration date %s " % e)

            asset.Expiration = sys.maxsize

        # does not seem to happen in C#
        # engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(asset))

        engine.CurrentContext.EvaluationStack.PushT(asset.Expiration)

        return True

    def Contract_Create(self, engine: ExecutionEngine):

        script = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()

        if len(script) > 1024 * 1024:
            return False

        param_list = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()
        if len(param_list) > 252:
            return False
        return_type = int(engine.CurrentContext.EvaluationStack.Pop().GetBigInteger())
        contract_properties = int(engine.CurrentContext.EvaluationStack.Pop().GetBigInteger())

        if len(engine.CurrentContext.EvaluationStack.Peek().GetByteArray()) > 252:
            return False
        name = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()

        if len(engine.CurrentContext.EvaluationStack.Peek().GetByteArray()) > 252:
            return False
        code_version = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()

        if len(engine.CurrentContext.EvaluationStack.Peek().GetByteArray()) > 252:
            return False
        author = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()

        if len(engine.CurrentContext.EvaluationStack.Peek().GetByteArray()) > 252:
            return False
        email = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()

        if len(engine.CurrentContext.EvaluationStack.Peek().GetByteArray()) > 65536:
            return False

        description = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()

        hash = Crypto.ToScriptHash(script, unhex=False)

        contract = self._contracts.TryGet(hash.ToBytes())

        if contract is None:
            code = FunctionCode(script=script, param_list=param_list, return_type=return_type, contract_properties=contract_properties)

            contract = ContractState(code, contract_properties, name, code_version, author, email, description)

            self._contracts.GetAndChange(code.ScriptHash().ToBytes(), contract)

            self._contracts_created[hash.ToBytes()] = UInt160(data=engine.CurrentContext.ScriptHash())

        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(contract))

        self.events_to_dispatch.append(
            SmartContractEvent(SmartContractEvent.CONTRACT_CREATED, ContractParameter(ContractParameterType.InteropInterface, contract),
                               hash, Blockchain.Default().Height + 1,
                               engine.ScriptContainer.Hash if engine.ScriptContainer else None,
                               test_mode=engine.testMode))
        return True

    def Contract_Migrate(self, engine: ExecutionEngine):

        script = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()

        if len(script) > 1024 * 1024:
            return False

        param_list = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()

        if len(param_list) > 252:
            return False

        return_type = int(engine.CurrentContext.EvaluationStack.Pop().GetBigInteger())

        contract_properties = engine.CurrentContext.EvaluationStack.Pop().GetBigInteger()

        if len(engine.CurrentContext.EvaluationStack.Peek().GetByteArray()) > 252:
            return False

        name = engine.CurrentContext.EvaluationStack.Pop().GetByteArray().decode('utf-8')

        if len(engine.CurrentContext.EvaluationStack.Peek().GetByteArray()) > 252:
            return False
        version = engine.CurrentContext.EvaluationStack.Pop().GetByteArray().decode('utf-8')

        if len(engine.CurrentContext.EvaluationStack.Peek().GetByteArray()) > 252:
            return False
        author = engine.CurrentContext.EvaluationStack.Pop().GetByteArray().decode('utf-8')

        if len(engine.CurrentContext.EvaluationStack.Peek().GetByteArray()) > 252:
            return False
        email = engine.CurrentContext.EvaluationStack.Pop().GetByteArray().decode('utf-8')

        if len(engine.CurrentContext.EvaluationStack.Peek().GetByteArray()) > 65536:
            return False
        description = engine.CurrentContext.EvaluationStack.Pop().GetByteArray().decode('utf-8')

        hash = Crypto.ToScriptHash(script, unhex=False)

        contract = self._contracts.TryGet(hash.ToBytes())

        if contract is None:

            code = FunctionCode(script=script, param_list=param_list, return_type=return_type)

            contract = ContractState(code=code, contract_properties=contract_properties,
                                     name=name, version=version, author=author,
                                     email=email, description=description)

            self._contracts.Add(hash.ToBytes(), contract)

            self._contracts_created[hash.ToBytes()] = UInt160(data=engine.CurrentContext.ScriptHash())

            if contract.HasStorage:
                for key, val in self._storages.Find(engine.CurrentContext.ScriptHash()).items():
                    key = StorageKey(script_hash=hash, key=key)
                    item = StorageItem(val)
                    self._storages.Add(key.ToArray(), item)

        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(contract))

        self.events_to_dispatch.append(
            SmartContractEvent(SmartContractEvent.CONTRACT_MIGRATED, ContractParameter(ContractParameterType.InteropInterface, contract),
                               hash, Blockchain.Default().Height + 1,
                               engine.ScriptContainer.Hash if engine.ScriptContainer else None,
                               test_mode=engine.testMode))

        return self.Contract_Destroy(engine)

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

        if len(key) == 20:
            keystr = Crypto.ToAddress(UInt160(data=key))

            try:
                valStr = int.from_bytes(valStr, 'little')
            except Exception as e:
                pass

        self.events_to_dispatch.append(
            SmartContractEvent(SmartContractEvent.STORAGE_PUT, ContractParameter(ContractParameterType.String, '%s -> %s' % (keystr, valStr)),
                               context.ScriptHash, Blockchain.Default().Height + 1,
                               engine.ScriptContainer.Hash if engine.ScriptContainer else None,
                               test_mode=engine.testMode))

        return True

    def Storage_Delete(self, engine: ExecutionEngine):

        context = engine.CurrentContext.EvaluationStack.Pop().GetInterface()

        if not self.CheckStorageContext(context):
            return False

        key = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()

        storage_key = StorageKey(script_hash=context.ScriptHash, key=key)

        keystr = key
        if len(key) == 20:
            keystr = Crypto.ToAddress(UInt160(data=key))

        self.events_to_dispatch.append(SmartContractEvent(SmartContractEvent.STORAGE_DELETE, ContractParameter(ContractParameterType.String, keystr),
                                                          context.ScriptHash, Blockchain.Default().Height + 1,
                                                          engine.ScriptContainer.Hash if engine.ScriptContainer else None,
                                                          test_mode=engine.testMode))

        self._storages.Remove(storage_key.ToArray())

        return True
