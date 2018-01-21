import events
import binascii
import pdb

from logzero import logger

from neo.VM.InteropService import InteropService
from neo.SmartContract.Contract import Contract
from neo.SmartContract.NotifyEventArgs import NotifyEventArgs
from neo.SmartContract.StorageContext import StorageContext
from neo.Core.State.StorageKey import StorageKey
from neo.Core.State.StorageItem import StorageItem
from neo.Core.Blockchain import Blockchain
from neocore.Cryptography.Crypto import Crypto
from neocore.BigInteger import BigInteger
from neocore.UInt160 import UInt160
from neocore.UInt256 import UInt256
from neo.EventHub import dispatch_smart_contract_event, dispatch_smart_contract_notify
from neo.SmartContract.SmartContractEvent import SmartContractEvent, NotifyEvent
from neocore.Cryptography.ECCurve import ECDSA
from neo.SmartContract.TriggerType import Application, Verification

from neo.VM.InteropService import StackItem, stack_item_to_py


class StateReader(InteropService):

    notifications = None

    events_to_dispatch = []

    __Instance = None

    _hashes_for_verifying = None

    @staticmethod
    def Instance():
        if StateReader.__Instance is None:
            StateReader.__Instance = StateReader()
        return StateReader.__Instance

    def __init__(self):

        super(StateReader, self).__init__()

        self.notifications = []
        self.events_to_dispatch = []

        self.Register("Neo.Runtime.GetTrigger", self.Runtime_GetTrigger)
        self.Register("Neo.Runtime.CheckWitness", self.Runtime_CheckWitness)
        self.Register("Neo.Runtime.Notify", self.Runtime_Notify)
        self.Register("Neo.Runtime.Log", self.Runtime_Log)
        self.Register("Neo.Runtime.GetTime", self.Runtime_GetCurrentTime)

        self.Register("Neo.Blockchain.GetHeight", self.Blockchain_GetHeight)
        self.Register("Neo.Blockchain.GetHeader", self.Blockchain_GetHeader)
        self.Register("Neo.Blockchain.GetBlock", self.Blockchain_GetBlock)
        self.Register("Neo.Blockchain.GetTransaction", self.Blockchain_GetTransaction)
        self.Register("Neo.Blockchain.GetAccount", self.Blockchain_GetAccount)
        self.Register("Neo.Blockchain.GetValidators", self.Blockchain_GetValidators)
        self.Register("Neo.Blockchain.GetAsset", self.Blockchain_GetAsset)
        self.Register("Neo.Blockchain.GetContract", self.Blockchain_GetContract)

        self.Register("Neo.Header.GetIndex", self.Header_GetIndex)
        self.Register("Neo.Header.GetHash", self.Header_GetHash)
        self.Register("Neo.Header.GetVersion", self.Header_GetVersion)
        self.Register("Neo.Header.GetPrevHash", self.Header_GetPrevHash)
        self.Register("Neo.Header.GetMerkleRoot", self.Header_GetMerkleRoot)
        self.Register("Neo.Header.GetTimestamp", self.Header_GetTimestamp)
        self.Register("Neo.Header.GetConsensusData", self.Header_GetConsensusData)
        self.Register("Neo.Header.GetNextConsensus", self.Header_GetNextConsensus)

        self.Register("Neo.Block.GetTransactionCount", self.Block_GetTransactionCount)
        self.Register("Neo.Block.GetTransactions", self.Block_GetTransactions)
        self.Register("Neo.Block.GetTransaction", self.Block_GetTransaction)

        self.Register("Neo.Transaction.GetHash", self.Transaction_GetHash)
        self.Register("Neo.Transaction.GetType", self.Transaction_GetType)
        self.Register("Neo.Transaction.GetAttributes", self.Transaction_GetAttributes)
        self.Register("Neo.Transaction.GetInputs", self.Transaction_GetInputs)
        self.Register("Neo.Transaction.GetOutputs", self.Transaction_GetOutputs)
        self.Register("Neo.Transaction.GetReferences", self.Transaction_GetReferences)
        self.Register("Neo.Transaction.GetUnspentCoins", self.Transaction_GetUnspentCoins)

        self.Register("Neo.Attribute.GetData", self.Attribute_GetData)
        self.Register("Neo.Attribute.GetUsage", self.Attribute_GetUsage)

        self.Register("Neo.Input.GetHash", self.Input_GetHash)
        self.Register("Neo.Input.GetIndex", self.Input_GetIndex)

        self.Register("Neo.Output.GetAssetId", self.Output_GetAssetId)
        self.Register("Neo.Output.GetValue", self.Output_GetValue)
        self.Register("Neo.Output.GetScriptHash", self.Output_GetScriptHash)

        self.Register("Neo.Account.GetVotes", self.Account_GetVotes)
        self.Register("Neo.Account.GetBalance", self.Account_GetBalance)
        self.Register("Neo.Account.GetScriptHash", self.Account_GetScriptHash)

        self.Register("Neo.Asset.GetAssetId", self.Asset_GetAssetId)
        self.Register("Neo.Asset.GetAssetType", self.Asset_GetAssetType)
        self.Register("Neo.Asset.GetAmount", self.Asset_GetAmount)
        self.Register("Neo.Asset.GetAvailable", self.Asset_GetAvailable)
        self.Register("Neo.Asset.GetPrecision", self.Asset_GetPrecision)
        self.Register("Neo.Asset.GetOwner", self.Asset_GetOwner)
        self.Register("Neo.Asset.GetAdmin", self.Asset_GetAdmin)
        self.Register("Neo.Asset.GetIssuer", self.Asset_GetIssuer)

        self.Register("Neo.Contract.GetScript", self.Contract_GetScript)

        self.Register("Neo.Storage.GetContext", self.Storage_GetContext)
        self.Register("Neo.Storage.Get", self.Storage_Get)

        # OLD API

        self.Register("AntShares.Runtime.GetTrigger", self.Runtime_GetTrigger)
        self.Register("AntShares.Runtime.CheckWitness", self.Runtime_CheckWitness)
        self.Register("AntShares.Runtime.Notify", self.Runtime_Notify)
        self.Register("AntShares.Runtime.Log", self.Runtime_Log)

        self.Register("AntShares.Blockchain.GetHeight", self.Blockchain_GetHeight)
        self.Register("AntShares.Blockchain.GetHeader", self.Blockchain_GetHeader)
        self.Register("AntShares.Blockchain.GetBlock", self.Blockchain_GetBlock)
        self.Register("AntShares.Blockchain.GetTransaction", self.Blockchain_GetTransaction)
        self.Register("AntShares.Blockchain.GetAccount", self.Blockchain_GetAccount)
        self.Register("AntShares.Blockchain.GetValidators", self.Blockchain_GetValidators)
        self.Register("AntShares.Blockchain.GetAsset", self.Blockchain_GetAsset)
        self.Register("AntShares.Blockchain.GetContract", self.Blockchain_GetContract)

        self.Register("AntShares.Header.GetHash", self.Header_GetHash)
        self.Register("AntShares.Header.GetVersion", self.Header_GetVersion)
        self.Register("AntShares.Header.GetPrevHash", self.Header_GetPrevHash)
        self.Register("AntShares.Header.GetMerkleRoot", self.Header_GetMerkleRoot)
        self.Register("AntShares.Header.GetTimestamp", self.Header_GetTimestamp)
        self.Register("AntShares.Header.GetConsensusData", self.Header_GetConsensusData)
        self.Register("AntShares.Header.GetNextConsensus", self.Header_GetNextConsensus)

        self.Register("AntShares.Block.GetTransactionCount", self.Block_GetTransactionCount)
        self.Register("AntShares.Block.GetTransactions", self.Block_GetTransactions)
        self.Register("AntShares.Block.GetTransaction", self.Block_GetTransaction)

        self.Register("AntShares.Transaction.GetHash", self.Transaction_GetHash)
        self.Register("AntShares.Transaction.GetType", self.Transaction_GetType)
        self.Register("AntShares.Transaction.GetAttributes", self.Transaction_GetAttributes)
        self.Register("AntShares.Transaction.GetInputs", self.Transaction_GetInputs)
        self.Register("AntShares.Transaction.GetOutpus", self.Transaction_GetOutputs)
        self.Register("AntShares.Transaction.GetReferences", self.Transaction_GetReferences)

        self.Register("AntShares.Attribute.GetData", self.Attribute_GetData)
        self.Register("AntShares.Attribute.GetUsage", self.Attribute_GetUsage)

        self.Register("AntShares.Input.GetHash", self.Input_GetHash)
        self.Register("AntShares.Input.GetIndex", self.Input_GetIndex)

        self.Register("AntShares.Output.GetAssetId", self.Output_GetAssetId)
        self.Register("AntShares.Output.GetValue", self.Output_GetValue)
        self.Register("AntShares.Output.GetScriptHash", self.Output_GetScriptHash)

        self.Register("AntShares.Account.GetVotes", self.Account_GetVotes)
        self.Register("AntShares.Account.GetBalance", self.Account_GetBalance)
        self.Register("AntShares.Account.GetScriptHash", self.Account_GetScriptHash)

        self.Register("AntShares.Asset.GetAssetId", self.Asset_GetAssetId)
        self.Register("AntShares.Asset.GetAssetType", self.Asset_GetAssetType)
        self.Register("AntShares.Asset.GetAmount", self.Asset_GetAmount)
        self.Register("AntShares.Asset.GetAvailable", self.Asset_GetAvailable)
        self.Register("AntShares.Asset.GetPrecision", self.Asset_GetPrecision)
        self.Register("AntShares.Asset.GetOwner", self.Asset_GetOwner)
        self.Register("AntShares.Asset.GetAdmin", self.Asset_GetAdmin)
        self.Register("AntShares.Asset.GetIssuer", self.Asset_GetIssuer)

        self.Register("AntShares.Contract.GetScript", self.Contract_GetScript)

        self.Register("AntShares.Storage.GetContext", self.Storage_GetContext)
        self.Register("AntShares.Storage.Get", self.Storage_Get)

    def ExecutionCompleted(self, engine, success, error=None):

        height = Blockchain.Default().Height
        tx_hash = engine.ScriptContainer.Hash

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

        payload = []
        for item in engine.EvaluationStack.Items:
            payload_item = stack_item_to_py(item)
            payload.append(payload_item)

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
            if engine.Trigger == Application:
                self.events_to_dispatch.append(
                    SmartContractEvent(SmartContractEvent.EXECUTION_FAIL, [payload, error, engine._VMState],
                                       entry_script, height, tx_hash, success, engine.testMode))
            else:
                self.events_to_dispatch.append(
                    SmartContractEvent(SmartContractEvent.VERIFICATION_FAIL, [payload, error, engine._VMState],
                                       entry_script, height, tx_hash, success, engine.testMode))

        self.notifications = []

    def Runtime_GetTrigger(self, engine):

        engine.EvaluationStack.PushT(engine.Trigger)

        return True

    def CheckWitnessHash(self, engine, hash):

        if self._hashes_for_verifying is None:
            container = engine.ScriptContainer
            self._hashes_for_verifying = container.GetScriptHashesForVerifying()

        return True if hash in self._hashes_for_verifying else False

    def CheckWitnessPubkey(self, engine, pubkey):
        scripthash = Contract.CreateSignatureRedeemScript(pubkey)
        return self.CheckWitnessHash(engine, Crypto.ToScriptHash(scripthash))

    def Runtime_CheckWitness(self, engine):

        hashOrPubkey = engine.EvaluationStack.Pop().GetByteArray()

        if len(hashOrPubkey) == 66 or len(hashOrPubkey) == 40:
            hashOrPubkey = binascii.unhexlify(hashOrPubkey)

        result = False

        if len(hashOrPubkey) == 20:
            result = self.CheckWitnessHash(engine, UInt160(data=hashOrPubkey))

        elif len(hashOrPubkey) == 33:
            point = ECDSA.decode_secp256r1(hashOrPubkey, unhex=False).G
            result = self.CheckWitnessPubkey(engine, point)
        else:
            result = False

        engine.EvaluationStack.PushT(result)

        return True

    def Runtime_Notify(self, engine):

        state = engine.EvaluationStack.Pop()

        # Build and emit smart contract event
        state_py = stack_item_to_py(state)
        payload = state_py if isinstance(state_py, list) else [state_py]  # Runtime.Notify payload must be a list

        args = NotifyEventArgs(
            engine.ScriptContainer,
            UInt160(data=engine.CurrentContext.ScriptHash()),
            payload
        )

        self.notifications.append(args)

        return True

    def Runtime_Log(self, engine):
        message = engine.EvaluationStack.Pop().GetByteArray()

        hash = UInt160(data=engine.CurrentContext.ScriptHash())

        # Build and emit smart contract event
        self.events_to_dispatch.append(SmartContractEvent(SmartContractEvent.RUNTIME_LOG,
                                                          [message],
                                                          hash,
                                                          Blockchain.Default().Height,
                                                          engine.ScriptContainer.Hash,
                                                          test_mode=engine.testMode))

        return True

    def Runtime_GetCurrentTime(self, engine):
        if Blockchain.Default() is None:
            engine.EvaluationStack.PushT(0)
        else:
            current_time = Blockchain.Default().CurrentBlock.Timestamp
            if engine.Trigger == Verification:
                current_time += Blockchain.SECONDS_PER_BLOCK
            engine.EvaluationStack.PushT(current_time)

        return True

    def Blockchain_GetHeight(self, engine):
        if Blockchain.Default() is None:
            engine.EvaluationStack.PushT(0)
        else:
            engine.EvaluationStack.PushT(Blockchain.Default().Height)

        return True

    def Blockchain_GetHeader(self, engine):
        data = engine.EvaluationStack.Pop().GetByteArray()

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

        engine.EvaluationStack.PushT(StackItem.FromInterface(header))
        return True

    def Blockchain_GetBlock(self, engine):

        data = engine.EvaluationStack.Pop()

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

        engine.EvaluationStack.PushT(StackItem.FromInterface(block))
        return True

    def Blockchain_GetTransaction(self, engine):

        data = engine.EvaluationStack.Pop().GetByteArray()
        tx = None

        if Blockchain.Default() is not None:
            tx, height = Blockchain.Default().GetTransaction(UInt256(data=data))

        engine.EvaluationStack.PushT(StackItem.FromInterface(tx))
        return True

    def Blockchain_GetAccount(self, engine):
        hash = UInt160(data=engine.EvaluationStack.Pop().GetByteArray())
        address = Crypto.ToAddress(hash).encode('utf-8')

        account = Blockchain.Default().GetAccountState(address)
        if account:
            engine.EvaluationStack.PushT(StackItem.FromInterface(account))
        else:
            engine.EvaluationStack.PushT(False)

        return True

    def Blockchain_GetValidators(self, engine):

        validators = Blockchain.Default().GetValidators()

        items = [StackItem(validator.encode_point(compressed=True)) for validator in validators]

        engine.EvaluationStack.PushT(items)

        return True

    def Blockchain_GetAsset(self, engine):
        data = engine.EvaluationStack.Pop().GetByteArray()
        asset = None

        if Blockchain.Default() is not None:
            asset = Blockchain.Default().GetAssetState(UInt256(data=data))

        engine.EvaluationStack.PushT(StackItem.FromInterface(asset))
        return True

    def Blockchain_GetContract(self, engine):
        hash = UInt160(data=engine.EvaluationStack.Pop().GetByteArray())
        contract = None

        if Blockchain.Default() is not None:
            contract = Blockchain.Default().GetContract(hash)

        engine.EvaluationStack.PushT(StackItem.FromInterface(contract))
        return True

    def Header_GetIndex(self, engine):
        header = engine.EvaluationStack.Pop().GetInterface()
        if header is None:
            return False
        engine.EvaluationStack.PushT(header.Index)
        return True

    def Header_GetHash(self, engine):

        header = engine.EvaluationStack.Pop().GetInterface()
        if header is None:
            return False
        engine.EvaluationStack.PushT(header.Hash.ToArray())
        return True

    def Header_GetVersion(self, engine):

        header = engine.EvaluationStack.Pop().GetInterface()
        if header is None:
            return False
        engine.EvaluationStack.PushT(header.Version)
        return True

    def Header_GetPrevHash(self, engine):

        header = engine.EvaluationStack.Pop().GetInterface()
        if header is None:
            return False
        engine.EvaluationStack.PushT(header.PrevHash.ToArray())
        return True

    def Header_GetMerkleRoot(self, engine):

        header = engine.EvaluationStack.Pop().GetInterface()
        if header is None:
            return False
        engine.EvaluationStack.PushT(header.MerkleRoot.ToArray())
        return True

    def Header_GetTimestamp(self, engine):

        header = engine.EvaluationStack.Pop().GetInterface()
        if header is None:
            return False
        engine.EvaluationStack.PushT(header.Timestamp)

        return True

    def Header_GetConsensusData(self, engine):

        header = engine.EvaluationStack.Pop().GetInterface()
        if header is None:
            return False
        engine.EvaluationStack.PushT(header.ConsensusData)
        return True

    def Header_GetNextConsensus(self, engine):

        header = engine.EvaluationStack.Pop().GetInterface()
        if header is None:
            return False
        engine.EvaluationStack.PushT(header.NextConsensus.ToArray())
        return True

    def Block_GetTransactionCount(self, engine):

        block = engine.EvaluationStack.Pop().GetInterface()
        if block is None:
            return False
        engine.EvaluationStack.PushT(len(block.Transactions))
        return True

    def Block_GetTransactions(self, engine):

        block = engine.EvaluationStack.Pop().GetInterface()
        if block is None:
            return False

        txlist = [StackItem.FromInterface(tx) for tx in block.FullTransactions]
        engine.EvaluationStack.PushT(txlist)
        return True

    def Block_GetTransaction(self, engine):

        block = engine.EvaluationStack.Pop().GetInterface()
        index = engine.EvaluationStack.Pop().GetBigInteger()

        if block is None or index < 0 or index > len(block.Transactions):
            return False

        tx = StackItem.FromInterface(block.FullTransactions[index])
        engine.EvaluationStack.PushT(tx)
        return True

    def Transaction_GetHash(self, engine):

        tx = engine.EvaluationStack.Pop().GetInterface()
        if tx is None:
            return False

        engine.EvaluationStack.PushT(tx.Hash.ToArray())
        return True

    def Transaction_GetType(self, engine):

        tx = engine.EvaluationStack.Pop().GetInterface()
        if tx is None:
            return False

        type = int.from_bytes(tx.Type, 'little')
        engine.EvaluationStack.PushT(type)
        return True

    def Transaction_GetAttributes(self, engine):

        tx = engine.EvaluationStack.Pop().GetInterface()
        if tx is None:
            return False

        attr = [StackItem.FromInterface(attr) for attr in tx.Attributes]
        engine.EvaluationStack.PushT(attr)
        return True

    def Transaction_GetInputs(self, engine):

        tx = engine.EvaluationStack.Pop().GetInterface()
        if tx is None:
            return False

        inputs = [StackItem.FromInterface(input) for input in tx.inputs]
        engine.EvaluationStack.PushT(inputs)
        return True

    def Transaction_GetOutputs(self, engine):

        tx = engine.EvaluationStack.Pop().GetInterface()

        if tx is None:
            return False

        outputs = []
        for output in tx.outputs:
            stackoutput = StackItem.FromInterface(output)
            outputs.append(stackoutput)

        engine.EvaluationStack.PushT(outputs)
        return True

    def Transaction_GetReferences(self, engine):

        tx = engine.EvaluationStack.Pop().GetInterface()

        if tx is None:
            return False

        refs = [StackItem.FromInterface(tx.References[input]) for input in tx.inputs]

        engine.EvaluationStack.PushT(refs)
        return True

    def Transaction_GetUnspentCoins(self, engine):
        tx = engine.EvaluationStack.Pop().GetInterface()

        if tx is None:
            return False

        refs = [StackItem.FromInterface(unspent) for unspent in Blockchain.Default().GetAllUnspent(tx.Hash)]
        engine.EvaluationStack.PushT(refs)
        return True

    def Attribute_GetUsage(self, engine):

        attr = engine.EvaluationStack.Pop().GetInterface()
        if attr is None:
            return False
        engine.EvaluationStack.PushT(attr.Usage)
        return True

    def Attribute_GetData(self, engine):

        attr = engine.EvaluationStack.Pop().GetInterface()
        if attr is None:
            return False
        engine.EvaluationStack.PushT(attr.Data)
        return True

    def Input_GetHash(self, engine):

        input = engine.EvaluationStack.Pop().GetInterface()
        if input is None:
            return False
        engine.EvaluationStack.PushT(input.PrevHash.ToArray())
        return True

    def Input_GetIndex(self, engine):

        input = engine.EvaluationStack.Pop().GetInterface()
        if input is None:
            return False

        engine.EvaluationStack.PushT(int(input.PrevIndex))
        return True

    def Output_GetAssetId(self, engine):

        output = engine.EvaluationStack.Pop().GetInterface()

        if output is None:
            return False

        engine.EvaluationStack.PushT(output.AssetId.ToArray())
        return True

    def Output_GetValue(self, engine):

        output = engine.EvaluationStack.Pop().GetInterface()
        if output is None:
            return False

        engine.EvaluationStack.PushT(output.Value.GetData())
        return True

    def Output_GetScriptHash(self, engine):

        output = engine.EvaluationStack.Pop().GetInterface()

        if output is None:
            return False

        engine.EvaluationStack.PushT(output.ScriptHash.ToArray())
        return True

    def Account_GetScriptHash(self, engine):

        account = engine.EvaluationStack.Pop().GetInterface()
        if account is None:
            return False
        engine.EvaluationStack.PushT(account.ScriptHash.ToArray())
        return True

    def Account_GetVotes(self, engine):

        account = engine.EvaluationStack.Pop().GetInterface()
        if account is None:
            return False

        votes = [StackItem.FromInterface(v.EncodePoint(True)) for v in account.Votes]
        engine.EvaluationStack.PushT(votes)
        return True

    def Account_GetBalance(self, engine):

        account = engine.EvaluationStack.Pop().GetInterface()
        assetId = UInt256(data=engine.EvaluationStack.Pop().GetByteArray())

        if account is None:
            return False
        balance = account.BalanceFor(assetId)
        engine.EvaluationStack.PushT(balance.GetData())
        return True

    def Asset_GetAssetId(self, engine):

        asset = engine.EvaluationStack.Pop().GetInterface()
        if asset is None:
            return False
        engine.EvaluationStack.PushT(asset.AssetId.ToArray())
        return True

    def Asset_GetAssetType(self, engine):

        asset = engine.EvaluationStack.Pop().GetInterface()
        if asset is None:
            return False
        engine.EvaluationStack.PushT(asset.AssetType)
        return True

    def Asset_GetAmount(self, engine):

        asset = engine.EvaluationStack.Pop().GetInterface()
        if asset is None:
            return False
        engine.EvaluationStack.PushT(asset.Amount.GetData())
        return True

    def Asset_GetAvailable(self, engine):

        asset = engine.EvaluationStack.Pop().GetInterface()
        if asset is None:
            return False
        engine.EvaluationStack.PushT(asset.Available.GetData())
        return True

    def Asset_GetPrecision(self, engine):

        asset = engine.EvaluationStack.Pop().GetInterface()
        if asset is None:
            return False
        engine.EvaluationStack.PushT(asset.Precision)
        return True

    def Asset_GetOwner(self, engine):

        asset = engine.EvaluationStack.Pop().GetInterface()
        if asset is None:
            return False
        engine.EvaluationStack.PushT(asset.Owner.EncodePoint(True))
        return True

    def Asset_GetAdmin(self, engine):

        asset = engine.EvaluationStack.Pop().GetInterface()
        if asset is None:
            return False
        engine.EvaluationStack.PushT(asset.Admin.ToArray())
        return True

    def Asset_GetIssuer(self, engine):

        asset = engine.EvaluationStack.Pop().GetInterface()
        if asset is None:
            return False
        engine.EvaluationStack.PushT(asset.Issuer.ToArray())
        return True

    def Contract_GetScript(self, engine):

        contract = engine.EvaluationStack.Pop().GetInterface()
        if contract is None:
            return False
        engine.EvaluationStack.PushT(contract.Code.Script)
        return True

    def Storage_GetContext(self, engine):

        hash = UInt160(data=engine.CurrentContext.ScriptHash())
        context = StorageContext(script_hash=hash)

        engine.EvaluationStack.PushT(StackItem.FromInterface(context))

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

        contract = Blockchain.Default().GetContract(context.ScriptHash.ToBytes())

        if contract is not None:
            if not contract.HasStorage:
                return False
        else:
            return False

        key = engine.EvaluationStack.Pop().GetByteArray()
        storage_key = StorageKey(script_hash=context.ScriptHash, key=key)
        item = Blockchain.Default().GetStorageItem(storage_key)

        keystr = key

        valStr = bytearray(0)

        if item is not None:
            valStr = bytearray(item.Value)

        if len(key) == 20:
            keystr = Crypto.ToAddress(UInt160(data=key))

            try:
                valStr = int.from_bytes(valStr, 'little')
            except Exception as e:
                logger.error("Could not convert %s to number: %s " % (valStr, e))

        if item is not None:
            engine.EvaluationStack.PushT(bytearray(item.Value))

        else:
            engine.EvaluationStack.PushT(bytearray(0))

        self.events_to_dispatch.append(SmartContractEvent(SmartContractEvent.STORAGE_GET, ['%s -> %s' % (keystr, valStr)],
                                                          context.ScriptHash, Blockchain.Default().Height, engine.ScriptContainer.Hash, test_mode=engine.testMode))

        return True
