from logzero import logger

from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neo.Core.Blockchain import Blockchain
from neo.Core.TX.Transaction import TransactionType
from neo.Implementations.Blockchains.LevelDB.DBCollection import DBCollection
from neo.Implementations.Blockchains.LevelDB.CachedScriptTable import CachedScriptTable
from neocore.Fixed8 import Fixed8
from neocore.UInt160 import UInt160

from neo.Core.State.UnspentCoinState import UnspentCoinState
from neo.Core.State.AccountState import AccountState
from neo.Core.State.CoinState import CoinState
from neo.Core.State.SpentCoinState import SpentCoinState, SpentCoinItem
from neo.Core.State.AssetState import AssetState
from neo.Core.State.ValidatorState import ValidatorState
from neo.Core.State.ContractState import ContractState
from neo.Core.State.StorageItem import StorageItem
from neo.Implementations.Blockchains.LevelDB.DBPrefix import DBPrefix

from neo.SmartContract.StateMachine import StateMachine
from neo.SmartContract.ApplicationEngine import ApplicationEngine
from neo.SmartContract import TriggerType


class TestLevelDBBlockchain(LevelDBBlockchain):

    def Persist(self, block):

        sn = self._db.snapshot()

        accounts = DBCollection(self._db, sn, DBPrefix.ST_Account, AccountState)
        unspentcoins = DBCollection(self._db, sn, DBPrefix.ST_Coin, UnspentCoinState)
        spentcoins = DBCollection(self._db, sn, DBPrefix.ST_SpentCoin, SpentCoinState)
        assets = DBCollection(self._db, sn, DBPrefix.ST_Asset, AssetState)
        validators = DBCollection(self._db, sn, DBPrefix.ST_Validator, ValidatorState)
        contracts = DBCollection(self._db, sn, DBPrefix.ST_Contract, ContractState)
        storages = DBCollection(self._db, sn, DBPrefix.ST_Storage, StorageItem)

        amount_sysfee = self.GetSysFeeAmount(block.PrevHash) + block.TotalFees().value
        amount_sysfee_bytes = amount_sysfee.to_bytes(8, 'little')

        with self._db.write_batch() as wb:
            for tx in block.Transactions:

                unspentcoinstate = UnspentCoinState.FromTXOutputsConfirmed(tx.outputs)
                unspentcoins.Add(tx.Hash.ToBytes(), unspentcoinstate)

                # go through all the accounts in the tx outputs
                for output in tx.outputs:
                    account = accounts.GetAndChange(output.AddressBytes, AccountState(output.ScriptHash))

                    if account.HasBalance(output.AssetId):
                        account.AddToBalance(output.AssetId, output.Value)
                    else:
                        account.SetBalanceFor(output.AssetId, output.Value)

                # go through all tx inputs
                unique_tx_input_hashes = []
                for input in tx.inputs:
                    if input.PrevHash not in unique_tx_input_hashes:
                        unique_tx_input_hashes.append(input.PrevHash)

                for txhash in unique_tx_input_hashes:
                    prevTx, height = self.GetTransaction(txhash.ToBytes())
                    coin_refs_by_hash = [coinref for coinref in tx.inputs if
                                         coinref.PrevHash.ToBytes() == txhash.ToBytes()]
                    for input in coin_refs_by_hash:

                        uns = unspentcoins.GetAndChange(input.PrevHash.ToBytes())
                        uns.OrEqValueForItemAt(input.PrevIndex, CoinState.Spent)

                        if prevTx.outputs[input.PrevIndex].AssetId.ToBytes() == Blockchain.SystemShare().Hash.ToBytes():
                            sc = spentcoins.GetAndChange(input.PrevHash.ToBytes(),
                                                         SpentCoinState(input.PrevHash, height, []))
                            sc.Items.append(SpentCoinItem(input.PrevIndex, block.Index))

                        output = prevTx.outputs[input.PrevIndex]
                        acct = accounts.GetAndChange(prevTx.outputs[input.PrevIndex].AddressBytes,
                                                     AccountState(output.ScriptHash))
                        assetid = prevTx.outputs[input.PrevIndex].AssetId
                        acct.SubtractFromBalance(assetid, prevTx.outputs[input.PrevIndex].Value)

                # do a whole lotta stuff with tx here...
                if tx.Type == TransactionType.RegisterTransaction:

                    asset = AssetState(tx.Hash, tx.AssetType, tx.Name, tx.Amount,
                                       Fixed8(0), tx.Precision, Fixed8(0), Fixed8(0), UInt160(data=bytearray(20)),
                                       tx.Owner, tx.Admin, tx.Admin, block.Index + 2 * 2000000, False)

                    assets.Add(tx.Hash.ToBytes(), asset)

                elif tx.Type == TransactionType.IssueTransaction:

                    txresults = [result for result in tx.GetTransactionResults() if result.Amount.value < 0]
                    for result in txresults:
                        asset = assets.GetAndChange(result.AssetId.ToBytes())
                        asset.Available = asset.Available - result.Amount

                elif tx.Type == TransactionType.ClaimTransaction:

                    for input in tx.Claims:

                        sc = spentcoins.TryGet(input.PrevHash.ToBytes())
                        if sc and sc.HasIndex(input.PrevIndex):
                            sc.DeleteIndex(input.PrevIndex)
                            spentcoins.GetAndChange(input.PrevHash.ToBytes())

                elif tx.Type == TransactionType.EnrollmentTransaction:

                    validator = validators.GetAndChange(tx.PublicKey, ValidatorState(pub_key=tx.PublicKey))
                    #                        logger.info("VALIDATOR %s " % validator.ToJson())

                elif tx.Type == TransactionType.StateTransaction:
                    # @TODO Implement persistence for State Descriptors
                    pass

                elif tx.Type == TransactionType.PublishTransaction:

                    contract = ContractState(tx.Code, tx.NeedStorage, tx.Name, tx.CodeVersion,
                                             tx.Author, tx.Email, tx.Description)

                    contracts.GetAndChange(tx.Code.ScriptHash().ToBytes(), contract)

                elif tx.Type == TransactionType.InvocationTransaction:

                    script_table = CachedScriptTable(contracts)
                    service = StateMachine(accounts, validators, assets, contracts, storages, wb=wb)

                    engine = ApplicationEngine(
                        trigger_type=TriggerType.Application,
                        container=tx,
                        table=script_table,
                        service=service,
                        gas=tx.Gas,
                        testMode=True
                    )

                    engine.LoadScript(tx.Script, False)

                    # normally, this function does not return true/false
                    # for testing purposes, we try to execute and if an exception is raised
                    # we will return false, otherwise if success return true

                    # this is different than the 'success' bool returned by engine.Execute()
                    # the 'success' bool returned by engine.Execute() is a value indicating
                    # wether or not the invocation was successful, and if so, we then commit
                    # the changes made by the contract to the database
                    try:
                        success = engine.Execute()
                        # service.ExecutionCompleted(engine, success)
                        return True
                    except Exception as e:
                        # service.ExecutionCompleted(self, False, e)
                        return False
