import sys
import neo.Core.BlockBase
from neo.Core.TX.Transaction import Transaction, TransactionOutput
from neo.Core.TX.TransactionAttribute import TransactionAttribute
from neo.Core.TX.InvocationTransaction import InvocationTransaction
from neo.Core.CoinReference import CoinReference
from neo.SmartContract.Iterable import Enumerator, Iterator

import neo.Core.State

from neo.Core.State.ContractState import ContractState
from neo.Core.State.AssetState import AssetState
from neo.Core.FunctionCode import FunctionCode
from neo.Core.State.StorageItem import StorageItem
from neo.Core.State.StorageKey import StorageKey
from neo.Core.State.ValidatorState import ValidatorState
from neo.Core.AssetType import AssetType
from neo.Core.Cryptography.Crypto import Crypto
from neo.Core.Cryptography.ECCurve import ECDSA
from neo.Core.UInt160 import UInt160
from neo.Core.UInt256 import UInt256
from neo.Core.State.AccountState import AccountState
from neo.Core.Fixed8 import Fixed8
from neo.Blockchain import GetBlockchain
from neo.VM.InteropService import StackItem
from neo.VM.ExecutionEngine import ExecutionEngine
from neo.SmartContract.StorageContext import StorageContext
from neo.VM.InteropService import StackItem, ByteArray, Array, Map
from neo.SmartContract.Iterable.Wrapper import ArrayWrapper, MapWrapper
from neo.SmartContract.Iterable import KeysWrapper, ValuesWrapper
from neo.SmartContract.Iterable.ConcatenatedEnumerator import ConcatenatedEnumerator
from neo.SmartContract.Iterable.ConcatenatedIterator import ConcatenatedIterator
from neo.SmartContract.StateReader import StateReader
from neo.SmartContract.ContractParameter import ContractParameter, ContractParameterType
from neo.EventHub import SmartContractEvent
from neo.logging import log_manager
from neo.SmartContract.Iterable.StorageIterator import StorageIterator

logger = log_manager.getLogger('vm')


class StateMachine(StateReader):
    def __init__(self, trigger, snapshot):

        super(StateMachine, self).__init__(trigger, snapshot)
        self._contracts_created = {}

        self.RegisterWithPrice("Neo.Runtime.GetTrigger", self.Runtime_GetTrigger, 1)
        self.RegisterWithPrice("Neo.Runtime.CheckWitness", self.Runtime_CheckWitness, 200)
        self.RegisterWithPrice("Neo.Runtime.Notify", self.Runtime_Notify, 1)
        self.RegisterWithPrice("Neo.Runtime.Log", self.Runtime_Log, 1)
        self.RegisterWithPrice("Neo.Runtime.GetTime", self.Runtime_GetCurrentTime, 1)
        self.RegisterWithPrice("Neo.Runtime.Serialize", self.Runtime_Serialize, 1)
        self.RegisterWithPrice("Neo.Runtime.Deserialize", self.Runtime_Deserialize, 1)

        self.RegisterWithPrice("Neo.Blockchain.GetHeight", self.Blockchain_GetHeight, 1)
        self.RegisterWithPrice("Neo.Blockchain.GetHeader", self.Blockchain_GetHeader, 100)
        self.RegisterWithPrice("Neo.Blockchain.GetBlock", self.Blockchain_GetBlock, 200)
        self.RegisterWithPrice("Neo.Blockchain.GetTransaction", self.Blockchain_GetTransaction, 100)
        self.RegisterWithPrice("Neo.Blockchain.GetTransactionHeight", self.Blockchain_GetTransactionHeight, 100)
        self.RegisterWithPrice("Neo.Blockchain.GetAccount", self.Blockchain_GetAccount, 100)
        self.RegisterWithPrice("Neo.Blockchain.GetValidators", self.Blockchain_GetValidators, 100)
        self.RegisterWithPrice("Neo.Blockchain.GetAsset", self.Blockchain_GetAsset, 100)
        self.RegisterWithPrice("Neo.Blockchain.GetContract", self.Blockchain_GetContract, 100)

        self.RegisterWithPrice("Neo.Header.GetHash", self.Header_GetHash, 1)
        self.RegisterWithPrice("Neo.Header.GetVersion", self.Header_GetVersion, 1)
        self.RegisterWithPrice("Neo.Header.GetPrevHash", self.Header_GetPrevHash, 1)
        self.RegisterWithPrice("Neo.Header.GetMerkleRoot", self.Header_GetMerkleRoot, 1)
        self.RegisterWithPrice("Neo.Header.GetTimestamp", self.Header_GetTimestamp, 1)
        self.RegisterWithPrice("Neo.Header.GetIndex", self.Header_GetIndex, 1)
        self.RegisterWithPrice("Neo.Header.GetConsensusData", self.Header_GetConsensusData, 1)
        self.RegisterWithPrice("Neo.Header.GetNextConsensus", self.Header_GetNextConsensus, 1)

        self.RegisterWithPrice("Neo.Block.GetTransactionCount", self.Block_GetTransactionCount, 1)
        self.RegisterWithPrice("Neo.Block.GetTransactions", self.Block_GetTransactions, 1)
        self.RegisterWithPrice("Neo.Block.GetTransaction", self.Block_GetTransaction, 1)

        self.RegisterWithPrice("Neo.Transaction.GetHash", self.Transaction_GetHash, 1)
        self.RegisterWithPrice("Neo.Transaction.GetType", self.Transaction_GetType, 1)
        self.RegisterWithPrice("Neo.Transaction.GetAttributes", self.Transaction_GetAttributes, 1)
        self.RegisterWithPrice("Neo.Transaction.GetInputs", self.Transaction_GetInputs, 1)
        self.RegisterWithPrice("Neo.Transaction.GetOutputs", self.Transaction_GetOutputs, 1)
        self.RegisterWithPrice("Neo.Transaction.GetReferences", self.Transaction_GetReferences, 200)
        self.RegisterWithPrice("Neo.Transaction.GetUnspentCoins", self.Transaction_GetUnspentCoins, 200)
        self.RegisterWithPrice("Neo.Transaction.GetWitnesses", self.Transaction_GetWitnesses, 200)

        self.RegisterWithPrice("Neo.InvocationTransaction.GetScript", self.InvocationTransaction_GetScript, 1)
        self.RegisterWithPrice("Neo.Witness.GetVerificationScript", self.Witness_GetVerificationScript, 100)
        self.RegisterWithPrice("Neo.Attribute.GetUsage", self.Attribute_GetUsage, 1)
        self.RegisterWithPrice("Neo.Attribute.GetData", self.Attribute_GetData, 1)

        self.RegisterWithPrice("Neo.Input.GetHash", self.Input_GetHash, 1)
        self.RegisterWithPrice("Neo.Input.GetIndex", self.Input_GetIndex, 1)
        self.RegisterWithPrice("Neo.Output.GetAssetId", self.Output_GetAssetId, 1)
        self.RegisterWithPrice("Neo.Output.GetValue", self.Output_GetValue, 1)
        self.RegisterWithPrice("Neo.Output.GetScriptHash", self.Output_GetScriptHash, 1)

        self.RegisterWithPrice("Neo.Account.GetScriptHash", self.Account_GetScriptHash, 1)
        self.RegisterWithPrice("Neo.Account.GetVotes", self.Account_GetVotes, 1)
        self.RegisterWithPrice("Neo.Account.GetBalance", self.Account_GetBalance, 1)
        self.RegisterWithPrice("Neo.Account.IsStandard", self.Account_IsStandard, 100)

        self.Register("Neo.Asset.Create", self.Asset_Create)
        self.Register("Neo.Asset.Renew", self.Asset_Renew)
        self.RegisterWithPrice("Neo.Asset.GetAssetId", self.Asset_GetAssetId, 1)
        self.RegisterWithPrice("Neo.Asset.GetAssetType", self.Asset_GetAssetType, 1)
        self.RegisterWithPrice("Neo.Asset.GetAmount", self.Asset_GetAmount, 1)
        self.RegisterWithPrice("Neo.Asset.GetAvailable", self.Asset_GetAvailable, 1)
        self.RegisterWithPrice("Neo.Asset.GetPrecision", self.Asset_GetPrecision, 1)
        self.RegisterWithPrice("Neo.Asset.GetOwner", self.Asset_GetOwner, 1)
        self.RegisterWithPrice("Neo.Asset.GetAdmin", self.Asset_GetAdmin, 1)
        self.RegisterWithPrice("Neo.Asset.GetIssuer", self.Asset_GetIssuer, 1)

        self.Register("Neo.Contract.Create", self.Contract_Create)
        self.Register("Neo.Contract.Migrate", self.Contract_Migrate)
        self.RegisterWithPrice("Neo.Contract.Destroy", self.Contract_Destroy, 1)
        self.RegisterWithPrice("Neo.Contract.GetScript", self.Contract_GetScript, 1)
        self.RegisterWithPrice("Neo.Contract.IsPayable", self.Contract_IsPayable, 1)
        self.RegisterWithPrice("Neo.Contract.GetStorageContext", self.Contract_GetStorageContext, 1)

        self.RegisterWithPrice("Neo.Storage.GetContext", self.Storage_GetContext, 1)
        self.RegisterWithPrice("Neo.Storage.GetReadOnlyContext", self.Storage_GetReadOnlyContext, 1)
        self.RegisterWithPrice("Neo.Storage.Get", self.Storage_Get, 100)
        self.Register("Neo.Storage.Put", self.Storage_Put)
        self.RegisterWithPrice("Neo.Storage.Delete", self.Storage_Delete, 100)
        self.RegisterWithPrice("Neo.Storage.Find", self.Storage_Find, 1)
        self.RegisterWithPrice("Neo.StorageContext.AsReadOnly", self.StorageContext_AsReadOnly, 1)

        self.RegisterWithPrice("Neo.Enumerator.Create", self.Enumerator_Create, 1)
        self.RegisterWithPrice("Neo.Enumerator.Next", self.Enumerator_Next, 1)
        self.RegisterWithPrice("Neo.Enumerator.Value", self.Enumerator_Value, 1)
        self.RegisterWithPrice("Neo.Enumerator.Concat", self.Enumerator_Concat, 1)
        self.RegisterWithPrice("Neo.Iterator.Create", self.Iterator_Create, 1)
        self.RegisterWithPrice("Neo.Iterator.Key", self.Iterator_Key, 1)
        self.RegisterWithPrice("Neo.Iterator.Keys", self.Iterator_Keys, 1)
        self.RegisterWithPrice("Neo.Iterator.Values", self.Iterator_Values, 1)
        self.RegisterWithPrice("Neo.Iterator.Concat", self.Iterator_Concat, 1)

        # Aliases
        self.RegisterWithPrice("Neo.Iterator.Next", self.Enumerator_Next, 1)
        self.RegisterWithPrice("Neo.Iterator.Value", self.Enumerator_Value, 1)

        # Old APIs
        self.RegisterWithPrice("AntShares.Runtime.CheckWitness", self.Runtime_CheckWitness, 200)
        self.RegisterWithPrice("AntShares.Runtime.Notify", self.Runtime_Notify, 1)
        self.RegisterWithPrice("AntShares.Runtime.Log", self.Runtime_Log, 1)
        self.RegisterWithPrice("AntShares.Blockchain.GetHeight", self.Blockchain_GetHeight, 1)
        self.RegisterWithPrice("AntShares.Blockchain.GetHeader", self.Blockchain_GetHeader, 100)
        self.RegisterWithPrice("AntShares.Blockchain.GetBlock", self.Blockchain_GetBlock, 200)
        self.RegisterWithPrice("AntShares.Blockchain.GetTransaction", self.Blockchain_GetTransaction, 100)
        self.RegisterWithPrice("AntShares.Blockchain.GetAccount", self.Blockchain_GetAccount, 100)
        self.RegisterWithPrice("AntShares.Blockchain.GetValidators", self.Blockchain_GetValidators, 200)
        self.RegisterWithPrice("AntShares.Blockchain.GetAsset", self.Blockchain_GetAsset, 100)
        self.RegisterWithPrice("AntShares.Blockchain.GetContract", self.Blockchain_GetContract, 100)
        self.RegisterWithPrice("AntShares.Header.GetHash", self.Header_GetHash, 1)
        self.RegisterWithPrice("AntShares.Header.GetVersion", self.Header_GetVersion, 1)
        self.RegisterWithPrice("AntShares.Header.GetPrevHash", self.Header_GetPrevHash, 1)
        self.RegisterWithPrice("AntShares.Header.GetMerkleRoot", self.Header_GetMerkleRoot, 1)
        self.RegisterWithPrice("AntShares.Header.GetTimestamp", self.Header_GetTimestamp, 1)
        self.RegisterWithPrice("AntShares.Header.GetConsensusData", self.Header_GetConsensusData, 1)
        self.RegisterWithPrice("AntShares.Header.GetNextConsensus", self.Header_GetNextConsensus, 1)
        self.RegisterWithPrice("AntShares.Block.GetTransactionCount", self.Block_GetTransactionCount, 1)
        self.RegisterWithPrice("AntShares.Block.GetTransactions", self.Block_GetTransactions, 1)
        self.RegisterWithPrice("AntShares.Block.GetTransaction", self.Block_GetTransaction, 1)
        self.RegisterWithPrice("AntShares.Transaction.GetHash", self.Transaction_GetHash, 1)
        self.RegisterWithPrice("AntShares.Transaction.GetType", self.Transaction_GetType, 1)
        self.RegisterWithPrice("AntShares.Transaction.GetAttributes", self.Transaction_GetAttributes, 1)
        self.RegisterWithPrice("AntShares.Transaction.GetInputs", self.Transaction_GetInputs, 1)
        self.RegisterWithPrice("AntShares.Transaction.GetOutpus", self.Transaction_GetOutputs, 1)
        self.RegisterWithPrice("AntShares.Transaction.GetReferences", self.Transaction_GetReferences, 200)
        self.RegisterWithPrice("AntShares.Attribute.GetData", self.Attribute_GetData, 1)
        self.RegisterWithPrice("AntShares.Attribute.GetUsage", self.Attribute_GetUsage, 1)
        self.RegisterWithPrice("AntShares.Input.GetHash", self.Input_GetHash, 1)
        self.RegisterWithPrice("AntShares.Input.GetIndex", self.Input_GetIndex, 1)
        self.RegisterWithPrice("AntShares.Output.GetAssetId", self.Output_GetAssetId, 1)
        self.RegisterWithPrice("AntShares.Output.GetValue", self.Output_GetValue, 1)
        self.RegisterWithPrice("AntShares.Output.GetScriptHash", self.Output_GetScriptHash, 1)
        self.RegisterWithPrice("AntShares.Account.GetVotes", self.Account_GetVotes, 1)
        self.RegisterWithPrice("AntShares.Account.GetBalance", self.Account_GetBalance, 1)
        self.RegisterWithPrice("AntShares.Account.GetScriptHash", self.Account_GetScriptHash, 1)
        self.Register("AntShares.Asset.Create", self.Asset_Create)
        self.Register("AntShares.Asset.Renew", self.Asset_Renew)
        self.RegisterWithPrice("AntShares.Asset.GetAssetId", self.Asset_GetAssetId, 1)
        self.RegisterWithPrice("AntShares.Asset.GetAssetType", self.Asset_GetAssetType, 1)
        self.RegisterWithPrice("AntShares.Asset.GetAmount", self.Asset_GetAmount, 1)
        self.RegisterWithPrice("AntShares.Asset.GetAvailable", self.Asset_GetAvailable, 1)
        self.RegisterWithPrice("AntShares.Asset.GetPrecision", self.Asset_GetPrecision, 1)
        self.RegisterWithPrice("AntShares.Asset.GetOwner", self.Asset_GetOwner, 1)
        self.RegisterWithPrice("AntShares.Asset.GetAdmin", self.Asset_GetAdmin, 1)
        self.RegisterWithPrice("AntShares.Asset.GetIssuer", self.Asset_GetIssuer, 1)
        self.Register("AntShares.Contract.Create", self.Contract_Create)
        self.Register("AntShares.Contract.Migrate", self.Contract_Migrate)
        self.RegisterWithPrice("AntShares.Contract.Destroy", self.Contract_Destroy, 1)
        self.RegisterWithPrice("AntShares.Contract.GetScript", self.Contract_GetScript, 1)
        self.RegisterWithPrice("AntShares.Contract.GetStorageContext", self.Contract_GetStorageContext, 1)
        self.RegisterWithPrice("AntShares.Storage.GetContext", self.Storage_GetContext, 1)
        self.RegisterWithPrice("AntShares.Storage.Get", self.Storage_Get, 100)
        self.Register("AntShares.Storage.Put", self.Storage_Put)
        self.RegisterWithPrice("Neo.Storage.Delete", self.Storage_Delete, 100)

    def ExecutionCompleted(self, engine, success, error=None):
        super(StateMachine, self).ExecutionCompleted(engine, success, error)

    def Commit(self):
        self.Snapshot.Commit()

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

    def Blockchain_GetAccount(self, engine: ExecutionEngine):
        hash = UInt160(data=engine.CurrentContext.EvaluationStack.Pop().GetByteArray())
        address = Crypto.ToAddress(hash).encode('utf-8')

        account = self.Snapshot.Accounts.GetOrAdd(address, lambda: AccountState(script_hash=hash))
        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(account))
        return True

    def Blockchain_GetValidators(self, engine: ExecutionEngine):
        validators = self.Snapshot.GetValidators()

        items = [StackItem(validator.encode_point(compressed=True)) for validator in validators]

        engine.CurrentContext.EvaluationStack.PushT(items)

        return True

    def Blockchain_GetAsset(self, engine: ExecutionEngine):
        data = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()
        asset = None

        if GetBlockchain() is not None:
            asset = self.Snapshot.Assets.TryGet(UInt256(data=data))
        if asset is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(asset))
        return True

    def Header_GetVersion(self, engine: ExecutionEngine):
        header = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.Core.BlockBase.BlockBase)
        if header is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(header.Version)
        return True

    def Header_GetMerkleRoot(self, engine: ExecutionEngine):
        header = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.Core.BlockBase.BlockBase)
        if header is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(header.MerkleRoot.ToArray())
        return True

    def Header_GetConsensusData(self, engine: ExecutionEngine):
        header = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.Core.BlockBase.BlockBase)
        if header is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(header.ConsensusData)
        return True

    def Header_GetNextConsensus(self, engine: ExecutionEngine):
        header = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.Core.BlockBase.BlockBase)
        if header is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(header.NextConsensus.ToArray())
        return True

    def Transaction_GetType(self, engine: ExecutionEngine):
        tx = engine.CurrentContext.EvaluationStack.Pop().GetInterface(Transaction)
        if tx is None:
            return False

        if isinstance(tx.Type, bytes):
            engine.CurrentContext.EvaluationStack.PushT(int.from_bytes(tx.Type, 'little'))
        else:
            engine.CurrentContext.EvaluationStack.PushT(tx.Type)
        return True

    def Transaction_GetAttributes(self, engine: ExecutionEngine):
        tx = engine.CurrentContext.EvaluationStack.Pop().GetInterface(Transaction)
        if tx is None:
            return False

        if len(tx.Attributes) > engine.maxArraySize:
            return False

        attr = [StackItem.FromInterface(attr) for attr in tx.Attributes]
        engine.CurrentContext.EvaluationStack.PushT(attr)
        return True

    def Transaction_GetInputs(self, engine: ExecutionEngine):
        tx = engine.CurrentContext.EvaluationStack.Pop().GetInterface(Transaction)
        if tx is None:
            return False

        if len(tx.inputs) > engine.maxArraySize:
            return False

        inputs = [StackItem.FromInterface(input) for input in tx.inputs]
        engine.CurrentContext.EvaluationStack.PushT(inputs)
        return True

    def Transaction_GetOutputs(self, engine: ExecutionEngine):
        tx = engine.CurrentContext.EvaluationStack.Pop().GetInterface(Transaction)

        if tx is None:
            return False

        if len(tx.outputs) > engine.maxArraySize:
            return False

        outputs = []
        for output in tx.outputs:
            stackoutput = StackItem.FromInterface(output)
            outputs.append(stackoutput)

        engine.CurrentContext.EvaluationStack.PushT(outputs)
        return True

    def Transaction_GetReferences(self, engine: ExecutionEngine):
        tx = engine.CurrentContext.EvaluationStack.Pop().GetInterface(Transaction)

        if tx is None:
            return False

        if len(tx.inputs) > engine.maxArraySize:
            return False

        refs = [StackItem.FromInterface(tx.References[input]) for input in tx.inputs]

        engine.CurrentContext.EvaluationStack.PushT(refs)
        return True

    def Transaction_GetUnspentCoins(self, engine: ExecutionEngine):
        tx = engine.CurrentContext.EvaluationStack.Pop().GetInterface(Transaction)

        if tx is None:
            return False

        outputs = GetBlockchain().GetAllUnspent(tx.Hash)
        if len(outputs) > engine.maxArraySize:
            return False

        refs = [StackItem.FromInterface(unspent) for unspent in outputs]
        engine.CurrentContext.EvaluationStack.PushT(refs)
        return True

    def Transaction_GetWitnesses(self, engine: ExecutionEngine):
        tx = engine.CurrentContext.EvaluationStack.Pop().GetInterface(Transaction)

        if tx is None:
            return False

        if len(tx.scripts) > engine.maxArraySize:
            return False

        witnesses = [StackItem.FromInterface(s) for s in tx.scripts]
        engine.CurrentContext.EvaluationStack.PushT(witnesses)
        return True

    def InvocationTransaction_GetScript(self, engine: ExecutionEngine):
        tx = engine.CurrentContext.EvaluationStack.Pop().GetInterface(InvocationTransaction)
        if tx is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(tx.Script)
        return True

    def Witness_GetVerificationScript(self, engine: ExecutionEngine):
        # TODO: create witness wrapper
        witness = engine.CurrentContext.EvaluationStack.Pop().GetInterface()
        if witness is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(witness.VerificationScript)
        return True

    def Attribute_GetUsage(self, engine: ExecutionEngine):
        attr = engine.CurrentContext.EvaluationStack.Pop().GetInterface(TransactionAttribute)
        if attr is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(attr.Usage)
        return True

    def Attribute_GetData(self, engine: ExecutionEngine):
        attr = engine.CurrentContext.EvaluationStack.Pop().GetInterface(TransactionAttribute)
        if attr is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(attr.Data)
        return True

    def Input_GetHash(self, engine: ExecutionEngine):
        input = engine.CurrentContext.EvaluationStack.Pop().GetInterface(CoinReference)
        if input is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(input.PrevHash.ToArray())
        return True

    def Input_GetIndex(self, engine: ExecutionEngine):
        input = engine.CurrentContext.EvaluationStack.Pop().GetInterface(CoinReference)
        if input is None:
            return False

        engine.CurrentContext.EvaluationStack.PushT(int(input.PrevIndex))
        return True

    def Output_GetAssetId(self, engine: ExecutionEngine):
        output = engine.CurrentContext.EvaluationStack.Pop().GetInterface(TransactionOutput)

        if output is None:
            return False

        engine.CurrentContext.EvaluationStack.PushT(output.AssetId.ToArray())
        return True

    def Output_GetValue(self, engine: ExecutionEngine):
        output = engine.CurrentContext.EvaluationStack.Pop().GetInterface(TransactionOutput)
        if output is None:
            return False

        engine.CurrentContext.EvaluationStack.PushT(output.Value.GetData())
        return True

    def Output_GetScriptHash(self, engine: ExecutionEngine):
        output = engine.CurrentContext.EvaluationStack.Pop().GetInterface(TransactionOutput)

        if output is None:
            return False

        engine.CurrentContext.EvaluationStack.PushT(output.ScriptHash.ToArray())
        return True

    def Account_GetScriptHash(self, engine: ExecutionEngine):
        account = engine.CurrentContext.EvaluationStack.Pop().GetInterface(AccountState)
        if account is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(account.ScriptHash.ToArray())
        return True

    def Account_GetVotes(self, engine: ExecutionEngine):
        account = engine.CurrentContext.EvaluationStack.Pop().GetInterface(AccountState)
        if account is None:
            return False

        votes = [StackItem.FromInterface(v.EncodePoint(True)) for v in account.Votes]
        engine.CurrentContext.EvaluationStack.PushT(votes)
        return True

    def Account_GetBalance(self, engine: ExecutionEngine):
        account = engine.CurrentContext.EvaluationStack.Pop().GetInterface(AccountState)
        assetId = UInt256(data=engine.CurrentContext.EvaluationStack.Pop().GetByteArray())

        if account is None:
            return False
        balance = account.BalanceFor(assetId)
        engine.CurrentContext.EvaluationStack.PushT(balance.GetData())
        return True

    def Account_IsStandard(self, engine: ExecutionEngine):
        # TODO: implement
        # contract_hash = UInt160(data=engine.CurrentContext.EvaluationStack.Pop().GetByteArray())
        # contract = self._contracts.TryGet(contract_hash.ToBytes())
        #
        # bool isStandard = contract is null | | contract.Script.IsStandardContract();
        # engine.CurrentContext.EvaluationStack.Push(isStandard);
        # return true;
        logger.error("Account_IsStandard not implemented!")
        return False

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

        try:
            owner = ECDSA.decode_secp256r1(ownerData, unhex=False).G
        except ValueError:
            return False

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
            expiration=GetBlockchain().Height + 1 + 2000000, is_frozen=False
        )

        asset = self.Snapshot.Assets.GetOrAdd(tx.Hash.ToBytes(), lambda: new_asset)
        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(asset))

        return True

    def Asset_Renew(self, engine: ExecutionEngine):

        current_asset = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.Core.State.AssetState.AssetState)

        if current_asset is None:
            return False

        years = engine.CurrentContext.EvaluationStack.Pop().GetBigInteger()

        asset = self.Snapshot.Assets.GetAndChange(current_asset.AssetId.ToBytes())

        if asset.Expiration < self.Snapshot.Height + 1:
            asset.Expiration = self.Snapshot.Height + 1

        try:

            asset.Expiration = asset.Expiration + years * 2000000

        except Exception as e:
            logger.error("could not set expiration date %s " % e)

            asset.Expiration = sys.maxsize

        # does not seem to happen in C#
        # engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(asset))

        engine.CurrentContext.EvaluationStack.PushT(asset.Expiration)

        return True

    def Asset_GetAssetId(self, engine: ExecutionEngine):
        asset = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.Core.State.AssetState.AssetState)
        if asset is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(asset.AssetId.ToArray())
        return True

    def Asset_GetAssetType(self, engine: ExecutionEngine):
        asset = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.Core.State.AssetState.AssetState)
        if asset is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(asset.AssetType)
        return True

    def Asset_GetAmount(self, engine: ExecutionEngine):
        asset = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.Core.State.AssetState.AssetState)
        if asset is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(asset.Amount.GetData())
        return True

    def Asset_GetAvailable(self, engine: ExecutionEngine):
        asset = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.Core.State.AssetState.AssetState)
        if asset is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(asset.Available.GetData())
        return True

    def Asset_GetPrecision(self, engine: ExecutionEngine):
        asset = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.Core.State.AssetState.AssetState)
        if asset is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(asset.Precision)
        return True

    def Asset_GetOwner(self, engine: ExecutionEngine):
        asset = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.Core.State.AssetState.AssetState)
        if asset is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(asset.Owner.EncodePoint(True))
        return True

    def Asset_GetAdmin(self, engine: ExecutionEngine):
        asset = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.Core.State.AssetState.AssetState)
        if asset is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(asset.Admin.ToArray())
        return True

    def Asset_GetIssuer(self, engine: ExecutionEngine):
        asset = engine.CurrentContext.EvaluationStack.Pop().GetInterface(neo.Core.State.AssetState.AssetState)
        if asset is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(asset.Issuer.ToArray())
        return True

    def Contract_Create(self, engine: ExecutionEngine):

        script = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()

        if len(script) > 1024 * 1024:
            return False

        param_list = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()
        if len(param_list) > 252:
            return False
        return_type = int(engine.CurrentContext.EvaluationStack.Pop().GetBigInteger())
        if return_type < 0 or return_type > 0xff:
            raise ValueError("Invalid return type data popped from stack")

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

        contract = self.Snapshot.Contracts.TryGet(hash.ToBytes())

        if contract is None:
            try:
                code = FunctionCode(script=script, param_list=param_list, return_type=return_type, contract_properties=contract_properties)
            except ValueError:
                # exception is caused by an invalid `return_type`. neo-cli accepts this , but we throw an exception
                # this is a dirty hack to work around the VM state difference that it causes until neo-cli hopefully fixes it
                # see https://github.com/neo-project/neo/issues/827
                code = FunctionCode(script=script, param_list=param_list, contract_properties=contract_properties)
                code.ReturnType = return_type

            contract = ContractState(code, contract_properties, name, code_version, author, email, description)

            self.Snapshot.Contracts.Add(code.ScriptHash().ToBytes(), contract)

            self._contracts_created[hash.ToBytes()] = UInt160(data=engine.CurrentContext.ScriptHash())

        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(contract))

        self.events_to_dispatch.append(
            SmartContractEvent(SmartContractEvent.CONTRACT_CREATED, ContractParameter(ContractParameterType.InteropInterface, contract),
                               hash, GetBlockchain().Height + 1,
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

        contract = self.Snapshot.Contracts.TryGet(hash.ToBytes())

        if contract is None:

            code = FunctionCode(script=script, param_list=param_list, return_type=return_type)

            contract = ContractState(code=code, contract_properties=contract_properties,
                                     name=name, version=version, author=author,
                                     email=email, description=description)

            self.Snapshot.Contracts.Add(hash.ToBytes(), contract)

            cur_hash = UInt160(data=engine.CurrentContext.ScriptHash())
            self._contracts_created[hash.ToBytes()] = cur_hash

            if contract.HasStorage:
                to_add = []
                for key, item in self.Snapshot.Storages.Find(cur_hash.ToArray()):
                    key = StorageKey(script_hash=hash, key=key[20:])
                    to_add.append((key.ToArray(), item))

                for k, v in to_add:
                    self.Snapshot.Storages.Add(k, v)

        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(contract))

        self.events_to_dispatch.append(
            SmartContractEvent(SmartContractEvent.CONTRACT_MIGRATED, ContractParameter(ContractParameterType.InteropInterface, contract),
                               hash, GetBlockchain().Height + 1,
                               engine.ScriptContainer.Hash if engine.ScriptContainer else None,
                               test_mode=engine.testMode))

        return self.Contract_Destroy(engine)

    def Contract_GetScript(self, engine: ExecutionEngine):
        contract = engine.CurrentContext.EvaluationStack.Pop().GetInterface(ContractState)
        if contract is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(contract.Code.Script)
        return True

    def Contract_IsPayable(self, engine: ExecutionEngine):
        contract = engine.CurrentContext.EvaluationStack.Pop().GetInterface(ContractState)
        if contract is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(contract.Payable)
        return True

    def Storage_Find(self, engine: ExecutionEngine):
        context = engine.CurrentContext.EvaluationStack.Pop().GetInterface(StorageContext)
        if context is None:
            return False

        if not self.CheckStorageContext(context):
            return False

        prefix = engine.CurrentContext.EvaluationStack.Pop().GetByteArray()
        prefix = context.ScriptHash.ToArray() + prefix

        enum = self.Snapshot.Storages.Find(prefix)
        iterator = StorageIterator(enum)
        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(iterator))

        return True

    def Enumerator_Create(self, engine: ExecutionEngine):
        item = engine.CurrentContext.EvaluationStack.Pop()
        if isinstance(item, Array):
            enumerator = ArrayWrapper(item)
            engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(enumerator))
            return True
        return False

    def Enumerator_Next(self, engine: ExecutionEngine):
        item = engine.CurrentContext.EvaluationStack.Pop().GetInterface(Enumerator)
        if item is None:
            return False
        engine.CurrentContext.EvaluationStack.PushT(item.Next())
        return True

    def Enumerator_Value(self, engine: ExecutionEngine):
        item = engine.CurrentContext.EvaluationStack.Pop().GetInterface(Enumerator)
        if item is None:
            return False

        engine.CurrentContext.EvaluationStack.PushT(item.Value())
        return True

    def Enumerator_Concat(self, engine: ExecutionEngine):
        item1 = engine.CurrentContext.EvaluationStack.Pop().GetInterface(Enumerator)
        if item1 is None:
            return False

        item2 = engine.CurrentContext.EvaluationStack.Pop().GetInterface(Enumerator)
        if item2 is None:
            return False

        result = ConcatenatedEnumerator(item1, item2)
        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(result))
        return True

    def Iterator_Create(self, engine: ExecutionEngine):
        item = engine.CurrentContext.EvaluationStack.Pop()
        if isinstance(item, Map):
            iterator = MapWrapper(item)
            engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(iterator))
            return True
        return False

    def Iterator_Key(self, engine: ExecutionEngine):
        try:
            iterator = engine.CurrentContext.EvaluationStack.Pop().GetInterface(Iterator)
        except TypeError:
            return False

        if iterator is None:
            return False

        engine.CurrentContext.EvaluationStack.PushT(iterator.Key())
        return True

    def Iterator_Keys(self, engine: ExecutionEngine):
        try:
            iterator = engine.CurrentContext.EvaluationStack.Pop().GetInterface(Iterator)
        except TypeError:
            return False

        if iterator is None:
            return False
        wrapper = StackItem.FromInterface(KeysWrapper(iterator))
        engine.CurrentContext.EvaluationStack.PushT(wrapper)
        return True

    def Iterator_Values(self, engine: ExecutionEngine):
        try:
            iterator = engine.CurrentContext.EvaluationStack.Pop().GetInterface(Iterator)
        except TypeError:
            return False

        if iterator is None:
            return False

        wrapper = StackItem.FromInterface(ValuesWrapper(iterator))
        engine.CurrentContext.EvaluationStack.PushT(wrapper)
        return True

    def Iterator_Concat(self, engine: ExecutionEngine):
        item1 = engine.CurrentContext.EvaluationStack.Pop().GetInterface(Iterator)
        if item1 is None:
            return False

        item2 = engine.CurrentContext.EvaluationStack.Pop().GetInterface(Iterator)
        if item2 is None:
            return False

        result = ConcatenatedIterator(item1, item2)
        engine.CurrentContext.EvaluationStack.PushT(StackItem.FromInterface(result))
        return True
