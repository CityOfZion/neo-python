from neo.VM.InteropService import InteropService
from neo.Wallets.Contract import Contract
from neo.SmartContract.NotifyEventArgs import NotifyEventArgs
from neo.SmartContract.LogEventArgs import LogEventArgs
from neo.SmartContract.StorageContext import StorageContext
from neo.Core.State.StorageKey import StorageKey
from neo.Core.State.StorageItem import StorageItem
from neo.Core.Blockchain import Blockchain
from neo.Cryptography.Crypto import Crypto
from neo.BigInteger import BigInteger
from neo.UInt160 import UInt160
from neo.UInt256 import UInt256
from neo.Cryptography.ECCurve import ECDSA

from neo.VM.InteropService import StackItem

import events

class StateReader(InteropService):


    NotifyEvent = events.Events()
    LogEvent = events.Events()

    __Instance = None


    _hashes_for_verifying=None

    @staticmethod
    def Instance():
        if StateReader.__Instance is None:
            StateReader.__Instance = StateReader()
        return StateReader.__Instance


    def __init__(self):

        super(StateReader, self).__init__()

        self.Register("Neo.Runtime.GetTrigger", self.Runtime_GetTrigger)
        self.Register("Neo.Runtime.CheckWitness", self.Runtime_CheckWitness)
        self.Register("Neo.Runtime.Notify", self.Runtime_Notify)
        self.Register("Neo.Runtime.Log", self.Runtime_Log)

        self.Register("Neo.Blockchain.GetHeight", self.Blockchain_GetHeight)
        self.Register("Neo.Blockchain.GetHeader", self.Blockchain_GetHeader)
        self.Register("Neo.Blockchain.GetBlock", self.Blockchain_GetBlock)
        self.Register("Neo.Blockchain.GetTransaction", self.Blockchain_GetTransaction)
        self.Register("Neo.Blockchain.GetAccount", self.Blockchain_GetAccount)
        self.Register("Neo.Blockchain.GetValidators", self.Blockchain_GetValidators)
        self.Register("Neo.Blockchain.GetAsset", self.Blockchain_GetAsset)
        self.Register("Neo.Blockchain.GetContract", self.Blockchain_GetContract)

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
        self.Register("Neo.Transaction.GetOutpus", self.Transaction_GetOutputs)
        self.Register("Neo.Transaction.GetReferences", self.Transaction_GetReferences)

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

        #OLD API

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



    def Runtime_GetTrigger(self, engine):
        engine.EvaluationStack.PushT(engine.Trigger)


    def CheckWitnessHash(self, engine, hash):

        if self._hashes_for_verifying is None:

            container = engine.ScriptContainer
            self._hashes_for_verifying = container.GetScriptHashesForVerifying()

        return True if hash in self._hashes_for_verifying else False


    def CheckWitnessPubkey(self, engine, pubkey):
        #the ToScriptHash thing needs fixing
        return self.CheckWitnessHash(engine, Crypto.ToScriptHash( Contract.CreateSignatureRedeemScript(pubkey)))


    def Runtime_CheckWitness(self, engine):

        hashOrPubkey = engine.EvaluationStack.Pop().GetByteArray()

        result = False

        if len(hashOrPubkey) == 20:

            result = self.CheckWitnessHash(engine, hashOrPubkey)

        elif len(hashOrPubkey) == 33:
            point = ECDSA.decode_secp256r1(hashOrPubkey)
            result = self.CheckWitnessPubkey(engine, point)

        else:
            result = False

        engine.EvaluationStack.PushT(result)

        return True


    def Runtime_Notify(self, engine):

        state = engine.EvaluationStack.Pop()
        notice = NotifyEventArgs(engine.ScriptContainer, UInt160(data=engine.CurrentContext.ScriptHash), state)
        self.NotifyEvent.on_change(notice)

        return True

    def Runtime_Log(self, engine):
        message = engine.EvaluationStack.Pop().GetByteArray().decode('utf-8')
        log = LogEventArgs(engine.ScriptContainer, UInt160(data=engine.CurrentContext.ScriptHash), message)
        self.LogEvent.on_change(log)

        return True

    def Blockchain_GetHeight(self, engine):
        if Blockchain.Default() is None:
            engine.EvaluationStack.PushT(0)
        else:
            engine.EvaluationStack.PushT( Blockchain.Default().Height )

        return True


    def Blockchain_GetHeader(self, engine):
        data = engine.EvaluationStack.Pop().GetByteArray()

        header = None

        if len(data) <= 5:

            height = BigInteger(data)

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


        engine.EvaluationStack.PushT( StackItem.FromInterface(header))
        return True


    def Blockchain_GetBlock(self, engine):
        data = engine.EvaluationStack.Pop().GetByteArray()


        block = None
        print("blockchain get block %s " % data)

        if len(data) <= 5:
            height = BigInteger.FromBytes(data)
            print("HEIGHT %s " % height)

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


        engine.EvaluationStack.PushT( StackItem.FromInterface(block))
        return True


    def Blockchain_GetTransaction(self, engine):

        data = engine.EvaluationStack.Pop().GetByteArray()
        tx = None

        if Blockchain.Default() is not None:
            tx = Blockchain.Default().GetTransaction( UInt256(data=data))

        engine.EvaluationStack.PushT(StackItem.FromInterface(tx))
        return True

    def Blockchain_GetAccount(self, engine):

        data = engine.EvaluationStack.Pop().GetByteArray()
        account = None

        if Blockchain.Default() is not None:
            account = Blockchain.Default().GetAccountState(UInt160(data=data))

        engine.EvaluationStack.PushT(StackItem.FromInterface(account))
        return True

    def Blockchain_GetValidators(self, engine):

        validators = Blockchain.Default().GetValidators()

        items = [ StackItem(validator.encode_point(compressed=True)) for validator in validators]

        engine.EvaluationStack.PushT(items)

        raise NotImplementedError()

    def Blockchain_GetAsset(self, engine):
        data = engine.EvaluationStack.Pop().GetByteArray()
        asset = None

        if Blockchain.Default() is not None:
            asset = Blockchain.Default().GetAssetState(UInt256(data=data))

        engine.EvaluationStack.PushT(StackItem.FromInterface(asset))
        return True

    def Blockchain_GetContract(self, engine):
        hash = UInt160(data = engine.EvaluationStack.Pop().GetByteArray())
        contract = None

        if Blockchain.Default() is not None:
            contract = Blockchain.Default().GetContract(hash)

        engine.EvaluationStack.PushT(StackItem.FromInterface(contract))
        return True

    def Header_GetHash(self, engine):

        header = engine.EvaluationStack.Pop().GetInterface('neo.Core.BlockBase.BlockBase')
        if header is None:
            return False
        engine.EvaluationStack.PushT(header.Hash.ToArray())
        return True


    def Header_GetVersion(self, engine):

        header = engine.EvaluationStack.Pop().GetInterface('neo.Core.BlockBase.BlockBase')
        if header is None:
            return False
        engine.EvaluationStack.PushT(header.Version)
        return True

    def Header_GetPrevHash(self, engine):

        header = engine.EvaluationStack.Pop().GetInterface('neo.Core.BlockBase.BlockBase')
        if header is None:
            return False
        engine.EvaluationStack.PushT(header.PrevHash.ToArray())
        return True

    def Header_GetMerkleRoot(self, engine):

        header = engine.EvaluationStack.Pop().GetInterface('neo.Core.BlockBase.BlockBase')
        if header is None:
            return False
        engine.EvaluationStack.PushT(header.MerkleRoot.ToArray())
        return True

    def Header_GetTimestamp(self, engine):

        header = engine.EvaluationStack.Pop().GetInterface('neo.Core.BlockBase.BlockBase')
        if header is None:
            return False
        engine.EvaluationStack.PushT(header.Timestamp)
        return True

    def Header_GetConsensusData(self, engine):

        header = engine.EvaluationStack.Pop().GetInterface('neo.Core.BlockBase.BlockBase')
        if header is None:
            return False
        engine.EvaluationStack.PushT(header.ConsensusData)
        return True

    def Header_GetNextConsensus(self, engine):

        header = engine.EvaluationStack.Pop().GetInterface('neo.Core.BlockBase.BlockBase')
        if header is None:
            return False
        engine.EvaluationStack.PushT(header.NextConsensus.ToArray())
        return True

    def Block_GetTransactionCount(self, engine):

        block = engine.EvaluationStack.Pop().GetInterface('neo.Core.Block.Block')
        if block is None:
            return False
        engine.EvaluationStack.PushT( len(block.Transactions))
        return True

    def Block_GetTransactions(self, engine):

        block = engine.EvaluationStack.Pop().GetInterface('neo.Core.Block.Block')
        if block is None:
            return False

        txlist = [StackItem.FromInterface(tx) for tx in block.Transactions]
        engine.EvaluationStack.PushT(txlist)
        return True

    def Block_GetTransaction(self, engine):

        block = engine.EvaluationStack.Pop().GetInterface('neo.Core.Block.Block')
        index = engine.EvaluationStack.Pop().GetBigInteger()

        if block is None or index < 0 or index > len(block.Transactions):
            return False

        tx= StackItem.FromInterface(block.Transactions[index])
        engine.EvaluationStack.PushT(tx)
        return True

    def Transaction_GetHash(self, engine):

        tx = engine.EvaluationStack.Pop().GetInterface('neo.Core.TX.Transaction.Transaction')
        if tx is None:
            return False

        engine.EvaluationStack.PushT(tx.Hash.ToArray())
        return True

    def Transaction_GetType(self, engine):

        tx = engine.EvaluationStack.Pop().GetInterface('neo.Core.TX.Transaction.Transaction')
        if tx is None:
            return False

        engine.EvaluationStack.PushT(tx.Type)
        return True

    def Transaction_GetAttributes(self, engine):

        tx = engine.EvaluationStack.Pop().GetInterface('neo.Core.TX.Transaction.Transaction')
        if tx is None:
            return False

        attr = [StackItem.FromInterface(attr) for attr in tx.Attributes]
        engine.EvaluationStack.PushT(attr)
        return True

    def Transaction_GetInputs(self, engine):

        tx = engine.EvaluationStack.Pop().GetInterface('neo.Core.TX.Transaction.Transaction')
        if tx is None:
            return False

        inputs = [StackItem.FromInterface(input) for input in tx.Inputs]
        engine.EvaluationStack.PushT(inputs)
        return True

    def Transaction_GetOutputs(self, engine):

        tx = engine.EvaluationStack.Pop().GetInterface('neo.Core.TX.Transaction.Transaction')
        if tx is None:
            return False

        outputs = [StackItem.FromInterface(output) for output in tx.Outputs]
        engine.EvaluationStack.PushT(outputs)
        return True

    def Transaction_GetReferences(self, engine):

        tx = engine.EvaluationStack.Pop().GetInterface('neo.Core.TX.Transaction.Transaction')
        if tx is None:
            return False

        refs = [StackItem.FromInterface(ref) for ref in tx.References]
        engine.EvaluationStack.PushT(refs)
        return True

    def Attribute_GetUsage(self, engine):

        attr = engine.EvaluationStack.Pop().GetInterface('neo.Core.TX.TransactionAttribute.TransactionAttribute')
        if attr is None:
            return False
        engine.EvaluationStack.PushT(attr.Usage)
        return True

    def Attribute_GetData(self, engine):

        attr = engine.EvaluationStack.Pop().GetInterface('neo.Core.TX.TransactionAttribute.TransactionAttribute')
        if attr is None:
            return False
        engine.EvaluationStack.PushT(attr.Data)
        return True

    def Input_GetHash(self, engine):

        input = engine.EvaluationStack.Pop().GetInterface('neo.Core.TX.Transaction.TransactionInput')
        if input is None:
            return False
        engine.EvaluationStack.PushT(input.PrevHash.ToArray())
        return True

    def Input_GetIndex(self, engine):

        input = engine.EvaluationStack.Pop().GetInterface('neo.Core.TX.Transaction.TransactionInput')
        if input is None:
            return False
        engine.EvaluationStack.PushT(input.PrevIndex)
        return True

    def Output_GetAssetId(self, engine):

        output = engine.EvaluationStack.Pop().GetInterface('neo.Core.TX.Transaction.TransactionOutput')
        if output is None:
            return False
        engine.EvaluationStack.PushT(output.AssetId)
        return True

    def Output_GetValue(self, engine):

        output = engine.EvaluationStack.Pop().GetInterface('neo.Core.TX.Transaction.TransactionOutput')
        if output is None:
            return False
        engine.EvaluationStack.PushT(output.Value.GetData())
        return True

    def Output_GetScriptHash(self, engine):

        output = engine.EvaluationStack.Pop().GetInterface('neo.Core.TX.Transaction.TransactionOutput')
        if output is None:
            return False
        engine.EvaluationStack.PushT(output.ScriptHash.ToArray())
        return True

    def Account_GetScriptHash(self, engine):

        account = engine.EvaluationStack.Pop().GetInterface('neo.Core.State.AccountState.AccountState')
        if account is None:
            return False
        engine.EvaluationStack.PushT(account.ScriptHash.ToArray())
        return True

    def Account_GetVotes(self, engine):

        account = engine.EvaluationStack.Pop().GetInterface('neo.Core.State.AccountState.AccountState')
        if account is None:
            return False

        votes = [StackItem.FromInterface(v.EncodePoint(True)) for v in account.Votes]
        engine.EvaluationStack.PushT(votes)
        return True

    def Account_GetBalance(self, engine):

        account = engine.EvaluationStack.Pop().GetInterface('neo.Core.State.AccountState.AccountState')
        assetId = UInt256( engine.EvaluationStack.Pop().GetByteArray())
        if account is None:
            return False

        balance = account.BalanceFor(assetId)
        engine.EvaluationStack.PushT(balance.GetData())
        return True

    def Asset_GetAssetId(self, engine):

        asset = engine.EvaluationStack.Pop().GetInterface('neo.Core.State.AssetState.AssetState')
        if asset is None:
            return False
        engine.EvaluationStack.PushT(asset.AssetId.ToArray())
        return True

    def Asset_GetAssetType(self, engine):

        asset = engine.EvaluationStack.Pop().GetInterface('neo.Core.State.AssetState.AssetState')
        if asset is None:
            return False
        engine.EvaluationStack.PushT(asset.AssetType)
        return True

    def Asset_GetAmount(self, engine):

        asset = engine.EvaluationStack.Pop().GetInterface('neo.Core.State.AssetState.AssetState')
        if asset is None:
            return False
        engine.EvaluationStack.PushT(asset.Amount.GetData())
        return True

    def Asset_GetAvailable(self, engine):

        asset = engine.EvaluationStack.Pop().GetInterface('neo.Core.State.AssetState.AssetState')
        if asset is None:
            return False
        engine.EvaluationStack.PushT(asset.Available.GetData())
        return True

    def Asset_GetPrecision(self, engine):

        asset = engine.EvaluationStack.Pop().GetInterface('neo.Core.State.AssetState.AssetState')
        if asset is None:
            return False
        engine.EvaluationStack.PushT(asset.Precision)
        return True

    def Asset_GetOwner(self, engine):

        asset = engine.EvaluationStack.Pop().GetInterface('neo.Core.State.AssetState.AssetState')
        if asset is None:
            return False
        engine.EvaluationStack.PushT(asset.Owner.EncodePoint(True))
        return True

    def Asset_GetAdmin(self, engine):

        asset = engine.EvaluationStack.Pop().GetInterface('neo.Core.State.AssetState.AssetState')
        if asset is None:
            return False
        engine.EvaluationStack.PushT(asset.Admin.ToArray())
        return True

    def Asset_GetIssuer(self, engine):

        asset = engine.EvaluationStack.Pop().GetInterface('neo.Core.State.AssetState.AssetState')
        if asset is None:
            return False
        engine.EvaluationStack.PushT(asset.Issuer.ToArray())
        return True

    def Contract_GetScript(self, engine):

        contract = engine.EvaluationStack.Pop().GetInterface('neo.Core.State.ContractState.ContractState')
        if contract is None:
            return False
        engine.EvaluationStack.PushT(contract.Code.Script)
        return True

    def Storage_GetContext(self, engine):

        print("GETting STORAGe conteXT%s " % engine.CurrentContext.ScriptHash())
        print("to bytes %s " % engine.CurrentContext.ScriptHash())
        hash = UInt160( data= engine.CurrentContext.ScriptHash())
        print("created hash %s " % hash)
        context = StorageContext(script_hash=hash)
        print("got context %s " % context)
        engine.EvaluationStack.PushT(StackItem.FromInterface(context))
        print("pushed context")
        return True

    def Storage_Get(self, engine):

        context = engine.EvaluationStack.Pop().GetInterface('neo.SmartContract.StorageContext.StorageContext')

        contract = Blockchain.Default().GetContract( context.ScriptHash.ToBytes())

        if contract is None or not contract.HasStorage:
            return False

        key = engine.EvaluationStack.Pop().GetByteArray()

        storage_key = StorageKey(script_hash=context.ScriptHash, key = key)

        item = Blockchain.Default().GetStorageItem(storage_key)

        if item is not None:

            engine.EvaluationStack.PushT( item.Value)

        else:
            engine.EvaluationStack.PushT( bytearray(0))

        return True
