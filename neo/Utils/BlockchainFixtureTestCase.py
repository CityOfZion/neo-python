import tarfile
import requests
import shutil
import binascii
import os
import neo
import struct
import asyncio

from contextlib import contextmanager
from neo.Utils.NeoTestCase import NeoTestCase
from neo.Storage.Implementation.DBFactory import getBlockchainDB
from neo.Storage.Interface.DBInterface import DBInterface
from neo.Storage.Common.DBPrefix import DBPrefix
from neo.SmartContract.ApplicationEngine import ApplicationEngine
from neo.Core.Blockchain import Blockchain
from neo.Core.Fixed8 import Fixed8
from neo.Implementations.Notifications.NotificationDB import NotificationDB
from neo.Settings import settings
from neo.logging import log_manager
from neo.Storage.Common.CachedScriptTable import CachedScriptTable
from neo.Core.State.CoinState import CoinState
from neo.Core.State.AccountState import AccountState
from neo.Core.State.UnspentCoinState import UnspentCoinState
from neo.Core.State.SpentCoinState import SpentCoinState, SpentCoinItem
from neo.Core.State.AssetState import AssetState
from neo.Core.State.ContractState import ContractPropertyState
from neo.Core.State.ContractState import ContractState
from neo.Core.State.StorageItem import StorageItem
from neo.Core.State.ValidatorState import ValidatorState
from neo.Core.TX.Transaction import Transaction, TransactionType
from neo.Network.nodemanager import NodeManager
from neo.SmartContract import TriggerType
from neo.Core.UInt160 import UInt160

logger = log_manager.getLogger()


def MonkeyPatchPersist(self, block, snapshot=None):

    if snapshot is None:
        snapshot = self._db.createSnapshot()
        snapshot.PersistingBlock = block

    amount_sysfee = self.GetSysFeeAmount(block.PrevHash) + (block.TotalFees().value / Fixed8.D)
    amount_sysfee_bytes = struct.pack("<d", amount_sysfee)

    with self._db.getBatch() as wb:
        for tx in block.Transactions:
            unspentcoinstate = UnspentCoinState.FromTXOutputsConfirmed(tx.outputs)
            snapshot.UnspentCoins.Add(tx.Hash.ToBytes(), unspentcoinstate)

            # go through all the accounts in the tx outputs
            for output in tx.outputs:
                account = snapshot.Accounts.GetAndChange(output.AddressBytes, lambda: AccountState(output.ScriptHash))

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

                    snapshot.UnspentCoins.GetAndChange(input.PrevHash.ToBytes()).Items[input.PrevIndex] |= CoinState.Spent

                    if prevTx.outputs[input.PrevIndex].AssetId.ToBytes() == Blockchain.SystemShare().Hash.ToBytes():
                        sc = snapshot.SpentCoins.GetAndChange(input.PrevHash.ToBytes(), lambda: SpentCoinState(input.PrevHash, height, []))
                        sc.Items.append(SpentCoinItem(input.PrevIndex, block.Index))

                    output = prevTx.outputs[input.PrevIndex]
                    acct = snapshot.Accounts.GetAndChange(prevTx.outputs[input.PrevIndex].AddressBytes, lambda: AccountState(output.ScriptHash))
                    assetid = prevTx.outputs[input.PrevIndex].AssetId
                    acct.SubtractFromBalance(assetid, prevTx.outputs[input.PrevIndex].Value)

            # do a whole lotta stuff with tx here...
            if tx.Type == TransactionType.RegisterTransaction:

                asset = AssetState(tx.Hash, tx.AssetType, tx.Name, tx.Amount,
                                   Fixed8(0), tx.Precision, Fixed8(0), Fixed8(0), UInt160(data=bytearray(20)),
                                   tx.Owner, tx.Admin, tx.Admin, block.Index + 2 * 2000000, False)

                snapshot.Assets.Add(tx.Hash.ToBytes(), asset)

            elif tx.Type == TransactionType.IssueTransaction:

                txresults = [result for result in tx.GetTransactionResults() if result.Amount.value < 0]
                for result in txresults:
                    asset = snapshot.Assets.GetAndChange(result.AssetId.ToBytes())
                    asset.Available = asset.Available - result.Amount

            elif tx.Type == TransactionType.ClaimTransaction:

                for input in tx.Claims:

                    sc = snapshot.SpentCoins.TryGet(input.PrevHash.ToBytes())
                    if sc and sc.HasIndex(input.PrevIndex):
                        sc.DeleteIndex(input.PrevIndex)
                        snapshot.SpentCoins.GetAndChange(input.PrevHash.ToBytes())

            elif tx.Type == TransactionType.EnrollmentTransaction:

                snapshot.Validators.GetAndChange(tx.PublicKey.ToBytes(), lambda: ValidatorState(pub_key=tx.PublicKey))
                #                        logger.info("VALIDATOR %s " % validator.ToJson())

            elif tx.Type == TransactionType.StateTransaction:
                # @TODO Implement persistence for State Descriptors
                pass

            elif tx.Type == TransactionType.PublishTransaction:
                def create_contract_state():
                    return ContractState(tx.Code, tx.NeedStorage, tx.Name, tx.CodeVersion, tx.Author, tx.Email, tx.Description)

                snapshot.Contracts.GetAndChange(tx.Code.ScriptHash().ToBytes(), create_contract_state)

            elif tx.Type == TransactionType.InvocationTransaction:
                return ApplicationEngine.Run(TriggerType.Application, tx, snapshot.Clone(), tx.Gas, True, wb)


def MonkeyPatchRun(trigger_type, tx, snapshot, gas, test_mode=True, wb=None):
    engine = ApplicationEngine(
        trigger_type=trigger_type,
        container=tx,
        snapshot=snapshot,
        gas=gas,
        testMode=test_mode
    )

    try:
        _script = binascii.unhexlify(tx.Script)
    except Exception as e:
        _script = tx.Script

    engine.LoadScript(_script)

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
        if test_mode:
            return True
        else:
            engine.testMode = True
            engine._Service.ExecutionCompleted(engine, success)
    except Exception as e:
        # service.ExecutionCompleted(self, False, e)
        if test_mode:
            return False
        else:
            engine.testMode = True
            engine._Service.ExecutionCompleted(engine, False, e)
    return engine


class BlockchainFixtureTestCase(NeoTestCase):
    FIXTURE_REMOTE_LOC = 'https://s3.us-east-2.amazonaws.com/cityofzion/fixtures/fixtures_v10.tar.gz'
    FIXTURE_FILENAME = os.path.join(settings.DATA_DIR_PATH, 'Chains/fixtures_v10.tar.gz')

    N_FIXTURE_REMOTE_LOC = 'https://s3.us-east-2.amazonaws.com/cityofzion/fixtures/notif_fixtures_v10.tar.gz'
    N_FIXTURE_FILENAME = os.path.join(settings.DATA_DIR_PATH, 'Chains/notif_fixtures_v10.tar.gz')
    N_NOTIFICATION_DB_NAME = os.path.join(settings.DATA_DIR_PATH, 'fixtures/test_notifications')

    _blockchain = None

    wallets_folder = os.path.dirname(neo.__file__) + '/Utils/fixtures/'

    _old_persist = None
    _old_run = None

    @classmethod
    @contextmanager
    def MPPersist(cls):
        # monkey patch Persist for test:
        cls._old_persist = Blockchain.Persist
        Blockchain.Persist = MonkeyPatchPersist

        # monkey patch Run for test:
        cls._old_run = ApplicationEngine.Run
        ApplicationEngine.Run = MonkeyPatchRun

        yield

        Blockchain.Persist = cls._old_persist
        ApplicationEngine.Run = cls._old_run

    def __init__(self, *args, **kwargs):
        super(BlockchainFixtureTestCase, self).__init__(*args, **kwargs)

    @classmethod
    def leveldb_testpath(cls):
        return 'Override Me!'

    @classmethod
    def setUpClass(cls):

        Blockchain.DeregisterBlockchain()

        super(BlockchainFixtureTestCase, cls).setUpClass()

        # for some reason during testing asyncio.get_event_loop() fails and does not create a new one if needed. This is the workaround
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        nodemgr = NodeManager()
        nodemgr.reset_for_test()

        # setup Blockchain DB
        if not os.path.exists(cls.FIXTURE_FILENAME):
            logger.info(
                "downloading fixture block database from %s. this may take a while" % cls.FIXTURE_REMOTE_LOC)

            response = requests.get(cls.FIXTURE_REMOTE_LOC, stream=True)

            response.raise_for_status()
            os.makedirs(os.path.dirname(cls.FIXTURE_FILENAME), exist_ok=True)
            with open(cls.FIXTURE_FILENAME, 'wb+') as handle:
                for block in response.iter_content(1024):
                    handle.write(block)

        try:
            tar = tarfile.open(cls.FIXTURE_FILENAME)
            tar.extractall(path=settings.DATA_DIR_PATH)
            tar.close()
        except Exception as e:
            raise Exception(
                "Could not extract tar file - %s. You may want need to remove the fixtures file %s manually to fix this." % (e, cls.FIXTURE_FILENAME))

        if not os.path.exists(cls.leveldb_testpath()):
            raise Exception("Error downloading fixtures at %s" % cls.leveldb_testpath())

        settings.setup_unittest_net()

        cls._blockchain = Blockchain(getBlockchainDB(path=cls.leveldb_testpath()), skip_version_check=True)

        cls._blockchain.UT = True
        Blockchain.RegisterBlockchain(cls._blockchain)

        # setup Notification DB
        if not os.path.exists(cls.N_FIXTURE_FILENAME):
            logger.info(
                "downloading fixture notification database from %s. this may take a while" % cls.N_FIXTURE_REMOTE_LOC)

            response = requests.get(cls.N_FIXTURE_REMOTE_LOC, stream=True)

            response.raise_for_status()
            with open(cls.N_FIXTURE_FILENAME, 'wb+') as handle:
                for block in response.iter_content(1024):
                    handle.write(block)

        try:
            tar = tarfile.open(cls.N_FIXTURE_FILENAME)
            tar.extractall(path=settings.DATA_DIR_PATH)
            tar.close()

        except Exception as e:
            raise Exception(
                "Could not extract tar file - %s. You may want need to remove the fixtures file %s manually to fix this." % (e, cls.N_FIXTURE_FILENAME))
        if not os.path.exists(cls.N_NOTIFICATION_DB_NAME):
            raise Exception("Error downloading fixtures at %s" % cls.N_NOTIFICATION_DB_NAME)

        settings.NOTIFICATION_DB_PATH = cls.N_NOTIFICATION_DB_NAME
        ndb = NotificationDB.instance()
        ndb.start()

    @classmethod
    def tearDownClass(cls):
        # tear down Blockchain DB
        Blockchain.Default().DeregisterBlockchain()
        if cls._blockchain is not None:
            cls._blockchain.UT = False
            cls._blockchain.Dispose()

        shutil.rmtree(cls.leveldb_testpath())

        # tear down Notification DB
        NotificationDB.instance().close()
        shutil.rmtree(cls.N_NOTIFICATION_DB_NAME)
