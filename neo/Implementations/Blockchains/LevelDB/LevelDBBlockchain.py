import time
import plyvel
import binascii

from logzero import logger

from neo.Core.Blockchain import Blockchain
from neo.Core.Header import Header
from neo.Core.Block import Block
from neo.Core.TX.Transaction import Transaction, TransactionType
from neocore.IO.BinaryWriter import BinaryWriter
from neocore.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import StreamManager
from neo.Implementations.Blockchains.LevelDB.DBCollection import DBCollection
from neo.Implementations.Blockchains.LevelDB.CachedScriptTable import CachedScriptTable
from neocore.Fixed8 import Fixed8
from neocore.UInt160 import UInt160
from neocore.UInt256 import UInt256

from neo.Core.State.UnspentCoinState import UnspentCoinState
from neo.Core.State.AccountState import AccountState
from neo.Core.State.CoinState import CoinState
from neo.Core.State.SpentCoinState import SpentCoinState, SpentCoinItem, SpentCoin
from neo.Core.State.AssetState import AssetState
from neo.Core.State.ValidatorState import ValidatorState
from neo.Core.State.ContractState import ContractState
from neo.Core.State.StorageItem import StorageItem
from neo.Implementations.Blockchains.LevelDB.DBPrefix import DBPrefix

from neo.SmartContract.StateMachine import StateMachine
from neo.SmartContract.ApplicationEngine import ApplicationEngine
from neo.SmartContract import TriggerType
from neocore.Cryptography.Crypto import Crypto
from neocore.BigInteger import BigInteger
from neo.EventHub import events


class LevelDBBlockchain(Blockchain):
    _path = None
    _db = None

    _header_index = []
    _block_cache = {}

    _current_block_height = 0
    _stored_header_count = 0

    _disposed = False

    _verify_blocks = False

    # this is the version of the database
    # should not be updated for network version changes
    _sysversion = b'/NEO:2.0.1/'

    _persisting_block = None

    @property
    def CurrentBlockHash(self):
        try:
            return self._header_index[self._current_block_height]
        except Exception as e:
            logger.info("Could not get current block hash, returning none: %s ", )

        return None

    @property
    def CurrentBlockHashPlusOne(self):
        try:
            return self._header_index[self._current_block_height + 1]
        except Exception as e:
            pass
        return self.CurrentBlockHash

    @property
    def CurrentHeaderHash(self):
        return self._header_index[len(self._header_index) - 1]

    @property
    def HeaderHeight(self):
        height = len(self._header_index) - 1
        return height

    @property
    def Height(self):
        return self._current_block_height

    @property
    def CurrentBlock(self):
        if self._persisting_block:
            return self._persisting_block
        return self.GetBlockByHeight(self.Height)

    @property
    def Path(self):
        return self._path

    def __init__(self, path):
        super(LevelDBBlockchain, self).__init__()
        self._path = path

        self._header_index = []
        self._header_index.append(Blockchain.GenesisBlock().Header.Hash.ToBytes())

        try:
            self._db = plyvel.DB(self._path, create_if_missing=True)
        #            self._db = plyvel.DB(self._path, create_if_missing=True, bloom_filter_bits=16, compression=None)
        except Exception as e:
            logger.info("leveldb unavailable, you may already be running this process: %s " % e)
            raise Exception('Leveldb Unavailable')

        version = self._db.get(DBPrefix.SYS_Version)

        if version == self._sysversion:  # or in the future, if version doesn't equal the current version...

            ba = bytearray(self._db.get(DBPrefix.SYS_CurrentBlock, 0))
            self._current_block_height = int.from_bytes(ba[-4:], 'little')

            ba = bytearray(self._db.get(DBPrefix.SYS_CurrentHeader, 0))
            current_header_height = int.from_bytes(ba[-4:], 'little')
            current_header_hash = bytes(ba[:64].decode('utf-8'), encoding='utf-8')

            #            logger.info("current header hash!! %s " % current_header_hash)
            #            logger.info("current header height, hashes %s %s %s" %(self._current_block_height, self._header_index, current_header_height) )

            hashes = []
            try:
                for key, value in self._db.iterator(prefix=DBPrefix.IX_HeaderHashList):
                    ms = StreamManager.GetStream(value)
                    reader = BinaryReader(ms)
                    hlist = reader.Read2000256List()
                    key = int.from_bytes(key[-4:], 'little')
                    hashes.append({'k': key, 'v': hlist})
                    StreamManager.ReleaseStream(ms)
            #                hashes.append({'index':int.from_bytes(key, 'little'), 'hash':value})

            except Exception as e:
                logger.info("Could not get stored header hash list: %s " % e)

            if len(hashes):
                hashes.sort(key=lambda x: x['k'])
                genstr = Blockchain.GenesisBlock().Hash.ToBytes()
                for hlist in hashes:

                    for hash in hlist['v']:
                        if hash != genstr:
                            self._header_index.append(hash)
                        self._stored_header_count += 1

            if self._stored_header_count == 0:
                headers = []
                for key, value in self._db.iterator(prefix=DBPrefix.DATA_Block):
                    dbhash = bytearray(value)[8:]
                    headers.append(Header.FromTrimmedData(binascii.unhexlify(dbhash), 0))

                headers.sort(key=lambda h: h.Index)
                for h in headers:
                    if h.Index > 0:
                        self._header_index.append(h.Hash.ToBytes())

            elif current_header_height > self._stored_header_count:

                try:
                    hash = current_header_hash
                    targethash = self._header_index[-1]

                    newhashes = []
                    while hash != targethash:
                        header = self.GetHeader(hash)
                        newhashes.insert(0, header)
                        hash = header.PrevHash.ToBytes()

                    self.AddHeaders(newhashes)
                except Exception as e:
                    pass
        else:
            with self._db.write_batch() as wb:
                for key, value in self._db.iterator():
                    wb.delete(key)

            self.Persist(Blockchain.GenesisBlock())
            self._db.put(DBPrefix.SYS_Version, self._sysversion)

    def GetAccountState(self, script_hash, print_all_accounts=False):

        if type(script_hash) is str:
            try:
                script_hash = script_hash.encode('utf-8')
            except Exception as e:
                logger.info("could not convert argument to bytes :%s " % e)
                return None

        sn = self._db.snapshot()
        accounts = DBCollection(self._db, sn, DBPrefix.ST_Account, AccountState)
        acct = accounts.TryGet(keyval=script_hash)

        sn.close()

        return acct

    def GetStorageItem(self, storage_key):
        sn = self._db.snapshot()
        storages = DBCollection(self._db, sn, DBPrefix.ST_Storage, StorageItem)
        item = storages.TryGet(storage_key.GetHashCodeBytes())
        sn.close()
        return item

    def SearchContracts(self, query):
        res = []
        sn = self._db.snapshot()
        contracts = DBCollection(self._db, sn, DBPrefix.ST_Contract, ContractState)
        keys = contracts.Keys

        query = query.casefold()

        for item in keys:

            contract = contracts.TryGet(keyval=item)
            try:
                if query in contract.Name.decode('utf-8').casefold():
                    res.append(contract)
                elif query in contract.Author.decode('utf-8').casefold():
                    res.append(contract)
                elif query in contract.Description.decode('utf-8').casefold():
                    res.append(contract)
                elif query in contract.Email.decode('utf-8').casefold():
                    res.append(contract)
            except Exception as e:
                logger.info("Could not query contract: %s " % e)

        sn.close()

        return res

    def ShowAllContracts(self):

        sn = self._db.snapshot()
        contracts = DBCollection(self._db, sn, DBPrefix.ST_Contract, ContractState)
        keys = contracts.Keys
        sn.close()
        return keys

    def GetContract(self, hash):

        if type(hash) is str:
            try:
                hash = UInt160.ParseString(hash).ToBytes()
            except Exception as e:
                logger.info("could not convert argument to bytes :%s " % e)
                return None

        sn = self._db.snapshot()
        contracts = DBCollection(self._db, sn, DBPrefix.ST_Contract, ContractState)
        contract = contracts.TryGet(keyval=hash)
        sn.close()
        return contract

    def GetAllSpentCoins(self):
        sn = self._db.snapshot()
        coins = DBCollection(self._db, sn, DBPrefix.ST_SpentCoin, SpentCoinState)

        return coins.Keys

    def GetUnspent(self, hash, index):

        sn = self._db.snapshot()
        coins = DBCollection(self._db, sn, DBPrefix.ST_Coin, UnspentCoinState)

        state = coins.TryGet(hash)

        if state is None:
            return None
        if index >= len(state.Items):
            return None
        if state.Items[index] & CoinState.Spent > 0:
            return None
        tx, height = self.GetTransaction(hash)

        return tx.outputs[index]

    def GetSpentCoins(self, tx_hash):

        if type(tx_hash) is not bytes:
            tx_hash = bytes(tx_hash.encode('utf-8'))

        sn = self._db.snapshot()
        coins = DBCollection(self._db, sn, DBPrefix.ST_SpentCoin, SpentCoinState)

        result = coins.TryGet(keyval=tx_hash)

        sn.close()

        return result

    def GetAllUnspent(self, hash):

        unspents = []

        sn = self._db.snapshot()
        unspentcoins = DBCollection(self._db, sn, DBPrefix.ST_Coin, UnspentCoinState)

        state = unspentcoins.TryGet(keyval=hash.ToBytes())

        if state:
            tx, height = self.GetTransaction(hash)

            for index, item in enumerate(state.Items):
                if item & CoinState.Spent == 0:
                    unspents.append(tx.outputs[index])
        else:
            print("no state?")
        return unspents

    def GetUnclaimed(self, hash):

        tx, height = self.GetTransaction(hash)

        if tx is None:
            return None

        out = {}
        sn = self._db.snapshot()
        coins = DBCollection(self._db, sn, DBPrefix.ST_SpentCoin, SpentCoinState)

        state = coins.TryGet(keyval=hash.ToBytes())

        if state:
            for item in state.Items:
                out[item.index] = SpentCoin(tx.outputs[item.index], height, item.height)

        sn.close()

        return out

    def SearchAssetState(self, query):
        res = []
        sn = self._db.snapshot()
        assets = DBCollection(self._db, sn, DBPrefix.ST_Asset, AssetState)
        keys = assets.Keys

        for item in keys:
            asset = assets.TryGet(keyval=item)
            if query in asset.Name.decode('utf-8'):
                res.append(asset)
            elif query in Crypto.ToAddress(asset.Issuer):
                res.append(asset)
            elif query in Crypto.ToAddress(asset.Admin):
                res.append(asset)
        sn.close()

        return res

    def GetAssetState(self, assetId):

        if type(assetId) is str:
            try:
                assetId = assetId.encode('utf-8')
            except Exception as e:
                logger.info("could not convert argument to bytes :%s " % e)
                return None

        sn = self._db.snapshot()
        assets = DBCollection(self._db, sn, DBPrefix.ST_Asset, AssetState)
        asset = assets.TryGet(assetId)

        return asset

    def GetTransaction(self, hash):

        if type(hash) is str:
            hash = hash.encode('utf-8')
        elif type(hash) is UInt256:
            hash = hash.ToBytes()

        out = self._db.get(DBPrefix.DATA_Transaction + hash)
        if out is not None:
            out = bytearray(out)
            height = int.from_bytes(out[:4], 'little')
            out = out[4:]
            outhex = binascii.unhexlify(out)
            return Transaction.DeserializeFromBufer(outhex, 0), height

        logger.info("Could not find transaction for hash %s " % hash)
        return None, -1

    def AddBlock(self, block):

        if not block.Hash.ToBytes() in self._block_cache:
            self._block_cache[block.Hash.ToBytes()] = block

        header_len = len(self._header_index)

        if block.Index - 1 >= header_len:
            return False

        if block.Index == header_len:

            if self._verify_blocks and not block.Verify():
                return False

            self.AddHeader(block.Header)

        return True

    def ContainsBlock(self, index):
        if index <= self._current_block_height:
            return True
        return False

    def ContainsTransaction(self, hash):
        tx = self._db.get(DBPrefix.DATA_Transaction + hash.ToBytes())
        return True if tx is not None else False

    def GetHeader(self, hash):

        try:
            out = bytearray(self._db.get(DBPrefix.DATA_Block + hash))
            out = out[8:]
            outhex = binascii.unhexlify(out)
            return Header.FromTrimmedData(outhex, 0)
        except TypeError as e2:
            pass
        except Exception as e:
            logger.info("OTHER ERRROR %s " % e)
        return None

    def GetHeaderBy(self, height_or_hash):
        hash = None

        intval = None
        try:
            intval = int(height_or_hash)
        except Exception as e:
            pass

        if not type(height_or_hash) == BigInteger and len(height_or_hash) == 64:
            bhash = height_or_hash.encode('utf-8')
            if bhash in self._header_index:
                hash = bhash

        elif intval is not None and self.GetHeaderHash(intval) is not None:
            hash = self.GetHeaderHash(int(height_or_hash))

        if hash is not None:
            return self.GetHeader(hash)

        return None

    def GetHeaderByHeight(self, height):

        if len(self._header_index) <= height:
            return False

        hash = self._header_index[height]

        return self.GetHeader(hash)

    def GetHeaderHash(self, height):
        if height < len(self._header_index) and height >= 0:
            return self._header_index[height]
        return None

    def GetBlockHash(self, height):
        """
        Get the block hash by its block height
        Args:
            height(int): height of the block to retrieve hash from.

        Returns:
            bytes: a non-raw block hash (i.e. b'6dd83ed8a3fc02e322f91f30431bf3662a8c8e8ebe976c3565f0d21c70620991', but not b'\x6d\xd8...etc'
        """
        if self._current_block_height < height:
            return

        if len(self._header_index) <= height:
            return

        return self._header_index[height]

    def GetSysFeeAmount(self, hash):

        if type(hash) is UInt256:
            hash = hash.ToBytes()
        try:
            value = self._db.get(DBPrefix.DATA_Block + hash)[0:8]
            amount = int.from_bytes(value, 'little', signed=False)
            return amount
        except Exception as e:
            logger.info("Could not get sys fee: %s " % e)

        return 0

    def GetBlockByHeight(self, height):
        """
        Get a block by its height.
        Args:
            height(int): the height of the block to retrieve.

        Returns:
            neo.Core.Block: block instance.
        """
        hash = self.GetBlockHash(height)
        if hash is not None:
            return self.GetBlockByHash(hash)

    def GetBlock(self, height_or_hash):

        hash = None

        intval = None
        try:
            intval = int(height_or_hash)
        except Exception as e:
            pass

        if intval is None and len(height_or_hash) == 64:
            bhash = height_or_hash.encode('utf-8')
            if bhash in self._header_index:
                hash = bhash
        elif intval is None and len(height_or_hash) == 66:
            bhash = height_or_hash[2:].encode('utf-8')
            if bhash in self._header_index:
                hash = bhash
        elif intval is not None and self.GetBlockHash(intval) is not None:
            hash = self.GetBlockHash(intval)

        if hash is not None:
            return self.GetBlockByHash(hash)

        return None

    def GetBlockByHash(self, hash):
        try:
            out = bytearray(self._db.get(DBPrefix.DATA_Block + hash))
            out = out[8:]
            outhex = binascii.unhexlify(out)
            return Block.FromTrimmedData(outhex, 0)
        except Exception as e:
            logger.info("Could not get block %s " % e)
        return None

    def GetNextBlockHash(self, hash):
        header = self.GetHeader(hash.ToBytes())
        if header:
            if header.Index + 1 >= len(self._header_index):
                return None
            return self._header_index[header.Index + 1]
        return None

    def AddHeader(self, header):
        self.AddHeaders([header])

    def AddHeaders(self, headers):

        newheaders = []
        count = 0
        for header in headers:

            if header.Index - 1 >= len(self._header_index) + count:
                logger.info(
                    "header is greater than header index length: %s %s " % (header.Index, len(self._header_index)))
                break

            if header.Index < count + len(self._header_index):
                continue
            if self._verify_blocks and not header.Verify():
                break

            count = count + 1

            newheaders.append(header)

        if len(newheaders):
            self.ProcessNewHeaders(newheaders)

        return True

    def ProcessNewHeaders(self, headers):
        start = time.clock()

        lastheader = headers[-1]

        hashes = [h.Hash.ToBytes() for h in headers]

        self._header_index = self._header_index + hashes

        logger.debug("Process Headers: %s %s" % (lastheader, (time.clock() - start)))

        if lastheader is not None:
            self.OnAddHeader(lastheader)

    def OnAddHeader(self, header):

        hHash = header.Hash.ToBytes()

        if hHash not in self._header_index:
            self._header_index.append(hHash)

        while header.Index - 2000 >= self._stored_header_count:
            ms = StreamManager.GetStream()
            w = BinaryWriter(ms)
            headers_to_write = self._header_index[self._stored_header_count:self._stored_header_count + 2000]
            w.Write2000256List(headers_to_write)
            out = ms.ToArray()
            StreamManager.ReleaseStream(ms)
            with self._db.write_batch() as wb:
                wb.put(DBPrefix.IX_HeaderHashList + self._stored_header_count.to_bytes(4, 'little'), out)

            self._stored_header_count += 2000

            logger.debug("Trimming stored header index %s" % self._stored_header_count)

        with self._db.write_batch() as wb:
            wb.put(DBPrefix.DATA_Block + hHash, bytes(8) + header.ToArray())
            wb.put(DBPrefix.SYS_CurrentHeader, hHash + header.Index.to_bytes(4, 'little'))

    @property
    def BlockCacheCount(self):
        return len(self._block_cache)

    def Persist(self, block):

        self._persisting_block = block

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

        to_dispatch = []

        with self._db.write_batch() as wb:

            wb.put(DBPrefix.DATA_Block + block.Hash.ToBytes(), amount_sysfee_bytes + block.Trim())

            for tx in block.Transactions:

                wb.put(DBPrefix.DATA_Transaction + tx.Hash.ToBytes(), block.IndexBytes() + tx.ToArray())

                # go through all outputs and add unspent coins to them

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
                    newvalidator = ValidatorState(pub_key=tx.PublicKey)
                    validators.GetAndChange(tx.PublicKey.ToBytes(), newvalidator)
                elif tx.Type == TransactionType.StateTransaction:
                    # @TODO Implement persistence for State Descriptors
                    pass

                elif tx.Type == TransactionType.PublishTransaction:
                    contract = ContractState(tx.Code, tx.NeedStorage, tx.Name, tx.CodeVersion,
                                             tx.Author, tx.Email, tx.Description)

                    contracts.GetAndChange(tx.Code.ScriptHash().ToBytes(), contract)
                elif tx.Type == TransactionType.InvocationTransaction:

                    script_table = CachedScriptTable(contracts)
                    service = StateMachine(accounts, validators, assets, contracts, storages, wb)

                    engine = ApplicationEngine(
                        trigger_type=TriggerType.Application,
                        container=tx,
                        table=script_table,
                        service=service,
                        gas=tx.Gas,
                        testMode=False
                    )

                    engine.LoadScript(tx.Script, False)

                    try:
                        success = engine.Execute()
                        service.ExecutionCompleted(engine, success)

                    except Exception as e:
                        service.ExecutionCompleted(engine, False, e)

                    to_dispatch = to_dispatch + service.events_to_dispatch
                else:

                    if tx.Type != b'\x00' and tx.Type != 128:
                        logger.info("TX Not Found %s " % tx.Type)

            # do save all the accounts, unspent, coins, validators, assets, etc
            # now sawe the current sys block

            # filter out accounts to delete then commit
            for key, account in accounts.Current.items():
                if not account.IsFrozen and len(account.Votes) == 0 and account.AllBalancesZeroOrLess():
                    accounts.Remove(key)

            accounts.Commit(wb)

            # filte out unspent coins to delete then commit
            for key, unspent in unspentcoins.Current.items():
                if unspent.IsAllSpent:
                    unspentcoins.Remove(key)
            unspentcoins.Commit(wb)

            # filter out spent coins to delete then commit to db
            for key, spent in spentcoins.Current.items():
                if len(spent.Items) == 0:
                    spentcoins.Remove(key)
            spentcoins.Commit(wb)

            # commit validators
            validators.Commit(wb)

            # commit assets
            assets.Commit(wb)

            # commit contracts
            contracts.Commit(wb)

            # commit storages ( not implemented )
            storages.Commit(wb)

            sn.close()

            wb.put(DBPrefix.SYS_CurrentBlock, block.Hash.ToBytes() + block.IndexBytes())
            self._current_block_height = block.Index
            self._persisting_block = None

            for event in to_dispatch:
                events.emit(event.event_type, event)

    def PersistBlocks(self):
        #        logger.info("PERRRRRSISST:: Hheight, b height, cache: %s/%s %s  --%s %s" % (self.Height, self.HeaderHeight, len(self._block_cache), self.CurrentHeaderHash, self.BlockSearchTries))

        while not self._disposed:

            if len(self._header_index) <= self._current_block_height + 1:
                break

            hash = self._header_index[self._current_block_height + 1]

            if hash not in self._block_cache:
                self.BlockSearchTries += 1
                break

            self.BlockSearchTries = 0
            block = self._block_cache[hash]

            try:
                self.Persist(block)
                self.OnPersistCompleted(block)
                del self._block_cache[hash]
            except Exception as e:
                logger.info("Could not persist block %s " % e)
                raise e

    def Dispose(self):
        self._db.close()
        self._disposed = True
