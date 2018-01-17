import sys

from logzero import logger

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
from neo.VM.InteropService import StackItem, stack_item_to_py
from neo.SmartContract.StorageContext import StorageContext
from neo.SmartContract.StateReader import StateReader
from neo.EventHub import dispatch_smart_contract_event, SmartContractEvent

import pdb


class StateMachine(StateReader):

    _accounts = None
    _validators = None
    _assets = None
    _contracts = None
    _storages = None

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

        self.Register("Neo.Account.SetVotes", self.Account_SetVotes)
        self.Register("Neo.Validator.Register", self.Validator_Register)
        self.Register("Neo.Asset.Create", self.Asset_Create)
        self.Register("Neo.Asset.Renew", self.Asset_Renew)
        self.Register("Neo.Contract.Create", self.Contract_Create)
        self.Register("Neo.Contract.Migrate", self.Contract_Migrate)
        self.Register("Neo.Contract.GetStorageContext", self.Contract_GetStorageContext)
        self.Register("Neo.Contract.Destroy", self.Contract_Destroy)
        self.Register("Neo.Storage.Put", self.Storage_Put)
        self.Register("Neo.Storage.Delete", self.Storage_Delete)

        self.Register("AntShares.Account.SetVotes", self.Account_SetVotes)
        self.Register("AntShares.Validator.Register", self.Validator_Register)
        self.Register("AntShares.Asset.Create", self.Asset_Create)
        self.Register("AntShares.Asset.Renew", self.Asset_Renew)
        self.Register("AntShares.Contract.Create", self.Contract_Create)
        self.Register("AntShares.Contract.Migrate", self.Contract_Migrate)
        self.Register("AntShares.Contract.GetStorageContext", self.Contract_GetStorageContext)
        self.Register("AntShares.Contract.Destroy", self.Contract_Destroy)
        self.Register("AntShares.Storage.Put", self.Storage_Put)
        self.Register("AntShares.Storage.Delete", self.Storage_Delete)

    def CheckStorageContext(self, context):
        if context is None:
            return False

        contract = self._contracts.TryGet(context.ScriptHash.ToBytes())

        if contract is not None:
            if contract.HasStorage:
                return True

        return False

    def ExecutionCompleted(self, engine, success, error=None):

        # commit storages right away
        if success:
            self.Commit()

        super(StateMachine, self).ExecutionCompleted(engine, success, error)

    def Commit(self):
        if self._wb is not None:
            self._accounts.Commit(self._wb, False)
            self._validators.Commit(self._wb, False)
            self._assets.Commit(self._wb, False)
            self._contracts.Commit(self._wb, False)
            self._storages.Commit(self._wb, False)

    def TestCommit(self):
        if self._storages.DebugStorage:
            self._storages.Commit(self._wb, False)

    def Blockchain_GetAccount(self, engine):
        hash = UInt160(data=engine.EvaluationStack.Pop().GetByteArray())
        address = Crypto.ToAddress(hash).encode('utf-8')

        account = self._accounts.TryGet(address)

        if account:
            engine.EvaluationStack.PushT(StackItem.FromInterface(account))
        else:
            print("no account")
            engine.EvaluationStack.PushT(False)

        return True

    def Blockchain_GetAsset(self, engine):

        hash = UInt256(data=engine.EvaluationStack.Pop().GetByteArray())

        asset = self._assets.TryGet(hash.ToBytes())
        if asset:
            engine.EvaluationStack.PushT(StackItem.FromInterface(asset))
        else:
            engine.EvaluationStack.PushT(False)
        return True

    def Blockchain_GetContract(self, engine):
        hash = UInt160(data=engine.EvaluationStack.Pop().GetByteArray())

        contract = self._contracts.TryGet(hash.ToBytes())

        if contract:
            engine.EvaluationStack.PushT(StackItem.FromInterface(contract))
        else:
            engine.EvaluationStack.PushT(False)
        return True

    def Account_SetVotes(self, engine):

        try:
            account = engine.EvaluationStack.Pop().GetInterface()

            vote_list = engine.EvaluationStack.Pop().GetArray()
        except Exception as e:
            logger.error("could not get account or votes: %s " % e)
            return False

        if account is None or len(vote_list) > 1024:
            return False

        if account.IsFrozen:
            return False

        balance = account.BalanceFor(Blockchain.SystemShare().Hash)

        if balance == Fixed8.Zero() and len(vote_list) > 0:
            return False

        acct = self._accounts.GetAndChange(account.AddressBytes)
        voteset = []
        for v in vote_list:
            if v not in voteset:
                voteset.append(v.GetByteArray())
        acct.Votes = voteset

        # print("*****************************************************")
        # print("SET ACCOUNT VOTES %s " % json.dumps(acct.ToJson(), indent=4))
        # print("*****************************************************")
        return True

    def Validator_Register(self, engine):

        pubkey = ECDSA.decode_secp256r1(engine.EvaluationStack.Pop().GetByteArray(), unhex=False, check_on_curve=True).G
        if pubkey.IsInfinity:
            return False

        if not self.CheckWitnessPubkey(engine, pubkey):
            return False

        vstate = ValidatorState(pub_key=pubkey)
        validator = self._validators.GetOrAdd(pubkey.ToBytes(), vstate)
        engine.EvaluationStack.PushT(StackItem.FromInterface(validator))
        return True

    def Asset_Create(self, engine):

        tx = engine.ScriptContainer

        asset_type = int(engine.EvaluationStack.Pop().GetBigInteger())

        if asset_type not in AssetType.AllTypes() or \
                asset_type == AssetType.CreditFlag or \
                asset_type == AssetType.DutyFlag or \
                asset_type == AssetType.GoverningToken or \
                asset_type == AssetType.UtilityToken:

            return False

        if len(engine.EvaluationStack.Peek().GetByteArray()) > 1024:
            return False

        name = engine.EvaluationStack.Pop().GetByteArray().decode('utf-8')

        amount = Fixed8(engine.EvaluationStack.Pop().GetBigInteger())

        if amount == Fixed8.Zero() or amount < Fixed8.NegativeSatoshi():
            return False

        if asset_type == AssetType.Invoice and amount != Fixed8.NegativeSatoshi():
            return False

        precision = int(engine.EvaluationStack.Pop().GetBigInteger())

        if precision > 8:
            return False

        if asset_type == AssetType.Share and precision != 0:
            return False

        if amount != Fixed8.NegativeSatoshi() and amount.value % pow(10, 8 - precision) != 0:
            return False

        ownerData = engine.EvaluationStack.Pop().GetByteArray()

        owner = ECDSA.decode_secp256r1(ownerData, unhex=False).G

        if owner.IsInfinity:
            return False

        if not self.CheckWitnessPubkey(engine, owner):
            logger.error("check witness false...")
            return False

        admin = UInt160(data=engine.EvaluationStack.Pop().GetByteArray())

        issuer = UInt160(data=engine.EvaluationStack.Pop().GetByteArray())

        new_asset = AssetState(
            asset_id=tx.Hash, asset_type=asset_type, name=name, amount=amount,
            available=Fixed8.Zero(), precision=precision, fee_mode=0, fee=Fixed8.Zero(),
            fee_addr=UInt160(), owner=owner, admin=admin, issuer=issuer,
            expiration=Blockchain.Default().Height + 1 + 2000000, is_frozen=False
        )

        asset = self._assets.GetOrAdd(tx.Hash.ToBytes(), new_asset)

        # print("*****************************************************")
        # print("CREATED ASSET %s " % tx.Hash.ToBytes())
        # print("*****************************************************")
        engine.EvaluationStack.PushT(StackItem.FromInterface(asset))

        return True

    def Asset_Renew(self, engine):

        current_asset = engine.EvaluationStack.Pop().GetInterface()

        if current_asset is None:
            return False

        years = engine.EvaluationStack.Pop().GetBigInteger()

        asset = self._assets.GetAndChange(current_asset.AssetId.ToBytes())

        if asset.Expiration < Blockchain.Default().Height + 1:
            asset.Expiration = Blockchain.Default().Height + 1

        try:

            asset.Expiration = asset.Expiration + years * 2000000

        except Exception as e:
            logger.error("could not set expiration date %s " % e)

            asset.Expiration = sys.maxsize

        # tx = engine.ScriptContainer
        # print("*****************************************************")
        # print("Renewed ASSET %s " % tx.Hash.ToBytes())
        # print("*****************************************************")
        engine.EvaluationStack.PushT(StackItem.FromInterface(asset))

        engine.EvaluationStack.PushT(asset.Expiration)

        return True

    def Contract_Create(self, engine):

        script = engine.EvaluationStack.Pop().GetByteArray()

        if len(script) > 1024 * 1024:
            return False

        param_list = engine.EvaluationStack.Pop().GetByteArray()
        if len(param_list) > 252:
            return False

        return_type = int(engine.EvaluationStack.Pop().GetBigInteger())

        contract_properties = int(engine.EvaluationStack.Pop().GetBigInteger())

        if len(engine.EvaluationStack.Peek().GetByteArray()) > 252:
            return False
        name = engine.EvaluationStack.Pop().GetByteArray()

        if len(engine.EvaluationStack.Peek().GetByteArray()) > 252:
            return False
        code_version = engine.EvaluationStack.Pop().GetByteArray()

        if len(engine.EvaluationStack.Peek().GetByteArray()) > 252:
            return False
        author = engine.EvaluationStack.Pop().GetByteArray()

        if len(engine.EvaluationStack.Peek().GetByteArray()) > 252:
            return False
        email = engine.EvaluationStack.Pop().GetByteArray()

        if len(engine.EvaluationStack.Peek().GetByteArray()) > 65536:
            return False

        description = engine.EvaluationStack.Pop().GetByteArray()

        hash = Crypto.ToScriptHash(script, unhex=False)

        contract = self._contracts.TryGet(hash.ToBytes())

        if contract is None:

            code = FunctionCode(script=script, param_list=param_list, return_type=return_type, contract_properties=contract_properties)

            contract = ContractState(code, contract_properties, name, code_version, author, email, description)

            self._contracts.GetAndChange(code.ScriptHash().ToBytes(), contract)

            self._contracts_created[hash.ToBytes()] = UInt160(data=engine.CurrentContext.ScriptHash())

        engine.EvaluationStack.PushT(StackItem.FromInterface(contract))

        # logger.info("*****************************************************")
        # logger.info("CREATED CONTRACT %s " % hash.ToBytes())
        # logger.info("*****************************************************")
        return True

    def Contract_Migrate(self, engine):

        script = engine.EvaluationStack.Pop().GetByteArray()

        if len(script) > 1024 * 1024:
            return False

        param_list = engine.EvaluationStack.Pop().GetByteArray()

        if len(param_list) > 252:
            return False

        return_type = int(engine.EvaluationStack.Pop().GetBigInteger())

        contract_properties = engine.EvaluationStack.Pop().GetBigInteger()

        if len(engine.EvaluationStack.Peek().GetByteArray()) > 252:
            return False
        name = engine.EvaluationStack.Pop().GetByteArray().decode('utf-8')

        if len(engine.EvaluationStack.Peek().GetByteArray()) > 252:
            return False
        version = engine.EvaluationStack.Pop().GetByteArray().decode('utf-8')

        if len(engine.EvaluationStack.Peek().GetByteArray()) > 252:
            return False
        author = engine.EvaluationStack.Pop().GetByteArray().decode('utf-8')

        if len(engine.EvaluationStack.Peek().GetByteArray()) > 252:
            return False
        email = engine.EvaluationStack.Pop().GetByteArray().decode('utf-8')

        if len(engine.EvaluationStack.Peek().GetByteArray()) > 65536:
            return False
        description = engine.EvaluationStack.Pop().GetByteArray().decode('utf-8')

        hash = Crypto.ToScriptHash(script, unhex=False)

        contract = self._contracts.TryGet(hash.ToBytes())

        if contract is None:

            code = FunctionCode(script=script, param_list=param_list, return_type=return_type)

            contract = ContractState(code=code, contract_properties=contract_properties,
                                     name=name, version=version, author=author,
                                     email=email, description=description)

            self._contracts.Add(hash.ToBytes(), contract)

            self._contracts_created[hash.ToBytes()] = UInt160(data=engine.CurrentContext.ScriptHash)

            if contract.HasStorage:

                for pair in self._storages.Find(engine.CurrentContext.ScriptHash()):

                    key = StorageKey(script_hash=hash, key=pair.Key.Key)
                    item = StorageItem(pair.Value.Value)
                    self._storages.Add(key, item)

        engine.EvaluationStack.PushT(StackItem.FromInterface(contract))

        # print("*****************************************************")
        # print("MIGRATED CONTRACT %s " % hash.ToBytes())
        # print("*****************************************************")

        return True

    def Contract_GetStorageContext(self, engine):

        contract = engine.EvaluationStack.Pop().GetInterface()

        if contract.ScriptHash.ToBytes() in self._contracts_created:

            created = self._contracts_created[contract.ScriptHash.ToBytes()]

            if created == UInt160(data=engine.CurrentContext.ScriptHash()):

                context = StorageContext(script_hash=contract.ScriptHash)
                engine.EvaluationStack.PushT(StackItem.FromInterface(context))

        return True

    def Contract_Destroy(self, engine):
        hash = UInt160(data=engine.CurrentContext.ScriptHash())

        contract = self._contracts.TryGet(hash.ToBytes())

        if contract is not None:

            self._contracts.Remove(hash.ToBytes())

            if contract.HasStorage:

                for pair in self._storages.Find(hash.ToBytes()):

                    self._storages.Remove(pair.Key)

        return True

    def Storage_Get(self, engine):

        context = None
        try:
            item = engine.EvaluationStack.Pop()
            context = item.GetInterface()
            shash = context.ScriptHash
        except Exception as e:
            logger.error("could not get storage context %s " % e)
            return False

        if not self.CheckStorageContext(context):
            return False

        key = engine.EvaluationStack.Pop().GetByteArray()
        storage_key = StorageKey(script_hash=context.ScriptHash, key=key)
        item = self._storages.TryGet(storage_key.GetHashCodeBytes())

        keystr = key

        valStr = bytearray(0)

        if item is not None:
            valStr = bytearray(item.Value)

        if len(key) == 20:
            keystr = Crypto.ToAddress(UInt160(data=key))

            try:
                valStr = int.from_bytes(valStr, 'little')
            except Exception as e:
                pass

        if item is not None:

            engine.EvaluationStack.PushT(bytearray(item.Value))

        else:
            engine.EvaluationStack.PushT(bytearray(0))

        self.events_to_dispatch.append(
            SmartContractEvent(SmartContractEvent.STORAGE_GET, ['%s -> %s' % (keystr, valStr)],
                               context.ScriptHash, Blockchain.Default().Height,
                               engine.ScriptContainer.Hash, test_mode=engine.testMode))

        return True

    def Storage_Put(self, engine):

        context = None
        try:

            context = engine.EvaluationStack.Pop().GetInterface()
        except Exception as e:
            logger.error("Storage Context Not found on stack")
            return False

        if not self.CheckStorageContext(context):
            return False

        key = engine.EvaluationStack.Pop().GetByteArray()
        if len(key) > 1024:
            return False

        value = engine.EvaluationStack.Pop().GetByteArray()

        new_item = StorageItem(value=value)
        storage_key = StorageKey(script_hash=context.ScriptHash, key=key)
        item = self._storages.GetOrAdd(storage_key.GetHashCodeBytes(), new_item)

        keystr = key
        valStr = bytearray(item.Value)

        if len(key) == 20:
            keystr = Crypto.ToAddress(UInt160(data=key))

            try:
                valStr = int.from_bytes(valStr, 'little')
            except Exception as e:
                pass

        self.events_to_dispatch.append(
            SmartContractEvent(SmartContractEvent.STORAGE_PUT, ['%s -> %s' % (keystr, valStr)],
                               context.ScriptHash, Blockchain.Default().Height,
                               engine.ScriptContainer.Hash, test_mode=engine.testMode))

        return True

    def Storage_Delete(self, engine):

        context = engine.EvaluationStack.Pop().GetInterface()

        if not self.CheckStorageContext(context):
            return False

        key = engine.EvaluationStack.Pop().GetByteArray()

        storage_key = StorageKey(script_hash=context.ScriptHash, key=key)

        keystr = key

        if len(key) == 20:
            keystr = Crypto.ToAddress(UInt160(data=key))

            self.events_to_dispatch.append(SmartContractEvent(SmartContractEvent.STORAGE_DELETE, [keystr],
                                                              context.ScriptHash, Blockchain.Default().Height,
                                                              engine.ScriptContainer.Hash, test_mode=engine.testMode))

        self._storages.Remove(storage_key.GetHashCodeBytes())

        return True
