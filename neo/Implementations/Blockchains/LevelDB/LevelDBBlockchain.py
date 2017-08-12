from neo.Core.Blockchain import Blockchain
from neo.Core.Header import Header
from neo.Core.Block import Block
from neo.Core.TX.Transaction import Transaction,TransactionType
from neo.IO.BinaryWriter import BinaryWriter
from neo.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import MemoryStream
from twisted.internet import reactor
from neo.Implementations.Blockchains.LevelDB.DBCollection import DBCollection
from neo.Fixed8 import Fixed8
import timeit

from neo.Core.State.UnspentCoinState import UnspentCoinState
from neo.Core.State.AccountState import AccountState
from neo.Core.State.CoinState import CoinState
from neo.Core.State.SpentCoinState import SpentCoinState
from neo.Core.State.AssetState import AssetState
from neo.Core.State.ValidatorState import ValidatorState
from neo.Core.State.ContractState import ContractState
import threading
import time
from .DBPrefix import DBPrefix

import plyvel
from autologging import logged
import binascii
import events
import asyncio
from memory_profiler import profile

from pympler import tracker



@logged
class LevelDBBlockchain(Blockchain):

    _path = None
    _db = None
    _thread = None
    _header_index = []
    _header_cache = {}
    _block_cache = {}
    _current_block_height = 0
    _stored_header_count = 0

    _disposed = False
    _async_loop = None

    _verify_blocks = False

    _memTracker = None

    _sysversion = b'/NEO:2.0.1/'

    SyncReset = events.Events()

    def CurrentBlockHash(self):
        try:
#        print("Getting Current bolck hash")
            return self._header_index[self._current_block_height]
        except Exception as e:
            pass
        return None
    def CurrentBlockHashPlusOne(self):
        try:
            return self._header_index[self._current_block_height + 1]
        except Exception as e:
            pass
        return self.CurrentBlockHash()

    def CurrentHeaderHash(self):
        return self._header_index[len(self._header_index) -1]

    def HeaderHeight(self):
        height = len(self._header_index) - 1
 #       print("Getting Header height: %s " % height)
        return height

    def Height(self):
        return self._current_block_height

    def Path(self):
        return self._path



#    @profile
    def __init__(self, path):
        super(LevelDBBlockchain,self).__init__()
        self._path = path
#        self.__log.debug('Initialized LEVELDB')

#        self._memTracker = tracker.SummaryTracker()

        self._header_index = []
        self._header_index.append(Blockchain.GenesisBlock().Header().HashToByteString())

        try:
            self._db = plyvel.DB(self._path, create_if_missing=True)
        except Exception as e:
            self.__log.debug("leveldb unavailable, you may already be running this process: %s " % e)
            raise Exception('Leveldb Unavailable')


        version = self._db.get(DBPrefix.SYS_Version)

        if version == self._sysversion: #or in the future, if version doesn't equal the current version...

            ba=bytearray(self._db.get(DBPrefix.SYS_CurrentBlock, 0))
            self._current_block_height = int.from_bytes( ba[-4:], 'little')


            ba = bytearray(self._db.get(DBPrefix.SYS_CurrentHeader, 0))
            current_header_height = int.from_bytes(ba[-4:], 'little')
            current_header_hash = bytes(ba[:64].decode('utf-8'), encoding='utf-8')

            self.__log.debug("current header hash!! %s " % current_header_hash)
            self.__log.debug("current header height, hashes %s %s %s" %(self._current_block_height, self._header_index, current_header_height) )


            hashes = []
            try:
                for key, value in self._db.iterator(prefix=DBPrefix.IX_HeaderHashList):
                    ms = MemoryStream(value)
                    reader = BinaryReader(ms)
                    hlist = reader.Read2000256List()
                    key =int.from_bytes(key[-4:], 'little')
                    hashes.append({'k':key, 'v':hlist})
    #                hashes.append({'index':int.from_bytes(key, 'little'), 'hash':value})

            except Exception as e:
                self.__log.debug("Coludnt get stored header hash list: %s " % e)

            if len(hashes):
                hashes.sort(key=lambda x:x['k'])
                genstr = Blockchain.GenesisBlock().HashToByteString()
                for hlist in hashes:

                    for hash in hlist['v']:
                        if hash != genstr:
                            self._header_index.append(hash)
                        self._stored_header_count += 1

            if self._stored_header_count == 0:
                headers = []
                for key, value in self._db.iterator(prefix=DBPrefix.DATA_Block):
                    dbhash = bytearray(value)[4:]
                    headers.append(  Header.FromTrimmedData(binascii.unhexlify(dbhash), 0))

                headers.sort(key=lambda h: h.Index)
                for h in headers:
                    if h.Index > 0:
                        self._header_index.append(h.HashToByteString())


        else:
            with self._db.write_batch() as wb:
                for key,value in self._db.iterator():
                    wb.delete(key)

            self.Persist(Blockchain.GenesisBlock())
            self._db.put(DBPrefix.SYS_Version, self._sysversion )



    def GetTransaction(self, hash):

        if type(hash) is not bytes:
            hash = bytes(hash.encode('utf-8'))

        if hash is not None:
            out = bytearray(self._db.get(DBPrefix.DATA_Transaction + hash))
            if out is not None:
                height = int.from_bytes(out[:4], 'little')
                out = out[4:]
                outhex = binascii.unhexlify(out)
                return Transaction.DeserializeFromBufer(outhex, 0), height

        return None, -1


    def AddBlock(self, block):

        #lock block cache
        if not block.HashToByteString() in self._block_cache:
#            self.__log.debug("adding block to block cache %s " % len(self._block_cache))
            self._block_cache[block.HashToByteString()] = block
        #end lock

        #lock header index
        header_len = len(self._header_index)
        if block.Index -1 >= header_len:
#            self.__log.debug("Returning... block index -1 is greater than header length")
            return False

        if block.Index == header_len:
#            self.__log.debug("Will try add block %s " % block.Index)

            if self._verify_blocks and not block.Verify():
#                self.__log.debug("Block did not verify, will not add")
                return False

            #do some leveldb stuff here
 #           self.__log.debug("this is where we add the block to leveldb")

            self.AddHeader(block.Header())

            if block.Index < header_len:
                #new_block_event.Set()
                #semaphore for therads or something
                pass

        #end lock header index

#        self.__log.debug("ADDED BLock %s %s" % (block.Index, block.HashToByteString()))
        return True

    def ContainsBlock(self,index):

        if index < self._current_block_height:
            return True
        return False

#    @profile
    def GetHeader(self, hash):

        #lock header cache
#        if hash in self._header_cache:
#            return self._header_cache[hash]
        #end lock header cache

#        self.__log.debug("get header from db not implementet yet")

        try:
            out = bytearray(self._db.get(DBPrefix.DATA_Block + hash))
            out = out[4:]
            outhex = binascii.unhexlify(out)
            return Header.FromTrimmedData(outhex, 0)
        except TypeError:
#            self.__log.debug("hash not found")
            pass
        except Exception as e:
            self.__log.debug("OTHER ERRROR %s " % e)
        return None

    def GetHeaderBy(self, height_or_hash):
        hash = None

        intval = None
        try:
            intval = int(height_or_hash)
        except Exception as e:
            pass

        if len(height_or_hash) == 64:
            bhash = height_or_hash.encode('utf-8')
            if bhash in self._header_index:
                hash = bhash

        elif intval is not None and self.GetHeaderHash(intval) is not None:
            hash = self.GetHeaderHash(int(height_or_hash))

        if hash is not None:
            return self.GetHeader(hash)

        return None

    def GetHeaderByHeight(self, height):
        hash=None
        #lock header index
        if len(self._header_index) <= height: return False

        hash =  self._header_index[height]
        #endlock

        return self.GetHeader(hash)

    def GetHeaderHash(self, height):
        if height < len(self._header_index) and height >= 0:
            return self._header_index[height]
        return None



    def GetBlockHash(self, height):
        if self._current_block_height < height: return False

        if len(self._header_index) <= height: return False

        return self._header_index[height]

    def GetSysFeeAmount(self, hash):
        return Fixed8(0)

    def GetBlock(self, height_or_hash):

        hash = None

        intval = None
        try:
            intval = int(height_or_hash)
        except Exception as e:
            pass

        if len(height_or_hash) == 64:
            bhash = height_or_hash.encode('utf-8')
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
            out = out[4:]
            outhex = binascii.unhexlify(out)
            return Block.FromTrimmedData(outhex, 0)
        except Exception as e:
            print("couldnt get block %s " % e)
        return None

    def AddHeader(self, header):
        self.AddHeaders( [ header])

#    @profile
    def AddHeaders(self, headers):

        # lock headers
        # lock header cache
        newheaders = []
        count = 0
        for header in headers:

            if header.Index - 1 >= len(self._header_index) + count:
                self.__log.debug("header in greater than header index length: %s %s " % (header.Index, len(self._header_index)))
                break

            if header.Index < count + len(self._header_index): continue
            if self._verify_blocks and not header.Verify(): break


#            self._header_cache[header.HashToByteString()] = header
            count = count+1
#            self.OnAddHeader(header)

            newheaders.append(header)


        # unlock headers cache
        # unlock headers

        if len(newheaders):
            self.OnAddHeaders(newheaders)

        newheaders = []
        headers = []

        return True



    def OnAddHeaders(self, headers):
        lastheader = None

        for h in headers:
            hHash = h.HashToByteString()
            if not hHash in self._header_index:
                self._header_index.append(hHash)
                lastheader = h

        if lastheader is not None:
            self.OnAddHeader(lastheader)

    def OnAddHeader(self, header):

        self.__log.debug("Will write header %s as last " % header.Index)
        hHash = header.HashToByteString()

        if not hHash in self._header_index:

            self._header_index.append(hHash)

        #just keep 2000 headrs in memory....
        while header.Index - 2000 >= self._stored_header_count:
            ms = MemoryStream()
            w = BinaryWriter(ms)
            headers_to_write = self._header_index[self._stored_header_count:self._stored_header_count+2000]
            w.Write2000256List(headers_to_write)
            ms.flush()
            self.__log.debug("Writing stored header count: %s " % self._stored_header_count)
            with self._db.write_batch() as wb:
                wb.put( DBPrefix.IX_HeaderHashList + self._stored_header_count.to_bytes(4, 'little'), ms.ToArray())

            self._stored_header_count += 2000

            self.__log.debug("TRimming stored header index!!!!! %s" % self._stored_header_count)

        with self._db.write_batch() as wb:
            wb.put( DBPrefix.DATA_Block + hHash, bytes(4) + header.ToArray())
            wb.put( DBPrefix.SYS_CurrentHeader,  hHash + header.Index.to_bytes( 4, 'little'))


    def BlockCacheCount(self):
        return len(self._block_cache)

#    @profile
    def Persist(self, block):

#        self._memTracker.print_diff()

#        start = time.clock()
#        self.__log.debug("___________________________________________")
        self.__log.debug("PERSISTING BLOCK %s " % block.Index)
#        self.__log.debug("Total Headers %s , block cache %s " % (self.HeaderHeight(), len(self._block_cache)))

        sn = self._db.snapshot()
        accounts = DBCollection(self._db, sn, DBPrefix.ST_Account, AccountState)
        unspentcoins = DBCollection(self._db, sn, DBPrefix.ST_Coin, UnspentCoinState)
        spentcoins = DBCollection(self._db, sn,  DBPrefix.ST_SpentCoin, SpentCoinState)
        assets = DBCollection(self._db, sn, DBPrefix.ST_Asset, AssetState )
        validators = DBCollection(self._db, sn, DBPrefix.ST_Validator, ValidatorState)
        contracts = DBCollection(self._db, sn, DBPrefix.ST_Contract, ContractState)

#        storages = sn.iterator(prefix=ST_Storage)

        amount_sysfee = (self.GetSysFeeAmount(block.PrevHash).value + block.TotalFees().value).to_bytes(4, 'little')

        with self._db.write_batch() as wb:

            wb.put(DBPrefix.DATA_Block + block.HashToByteString(), amount_sysfee + block.Trim())

            for tx in block.Transactions:

                wb.put(DBPrefix.DATA_Transaction + tx.HashToByteString(), block.IndexBytes() + tx.ToArray())

                #go through all outputs and add unspent coins to them

                unspentcoinstate = UnspentCoinState.FromTXOutputsConfirmed(tx.outputs)
                unspentcoins.Add(tx.HashToByteString(), unspentcoinstate)

                #go through all the accounts in the tx outputs
                for output in tx.outputs:
                    account = accounts.GetAndChange(output.ScriptHashBytes(), AccountState(output.ScriptHashRaw()))

                    if account.HasBalance(output.AssetId):
                        account.AddToBalance(output.AssetId, output.Value.value)
                    else:
                        account.SetBalanceFor(output.AssetId, output.Value)



                #go through all tx inputs
                unique_tx_input_hashes = []
                for input in tx.inputs:
                    if not input.PrevHash in unique_tx_input_hashes:
                        unique_tx_input_hashes.append(input.PrevHash)

                for txhash in unique_tx_input_hashes:
                    prevTx, height = self.GetTransaction(txhash)
                    coin_refs_by_hash = [coinref for coinref in tx.inputs if coinref.PrevHash == txhash]
                    for input in coin_refs_by_hash:

                        uns = unspentcoins.GetAndChange(input.PrevHash)
                        try:
                            uns.Items[input.PrevIndex] |= CoinState.Spent
                        except KeyError as e:
                            uns.Items[input.PrevIndex] = CoinState.Spent

                        if prevTx.outputs[input.PrevIndex].AssetId == Blockchain.SystemShare().HashToByteString():
                            sc = spentcoins.GetAndChange(input.PrevHash, SpentCoinState(input.PrevHash, height, {} ))
                            sc.Items[input.PrevIndex] = block.Index

                        acct = accounts.GetAndChange(prevTx.outputs[input.PrevIndex].ScriptHashBytes())
                        assetid = prevTx.outputs[input.PrevIndex].AssetId
                        acct.AddToBalance( assetid, -1 * prevTx.outputs[input.PrevIndex].Value.value)

                #do a whole lotta stuff with tx here...
                if tx.Type == int.from_bytes( TransactionType.RegisterTransaction, 'little'):

                    #tx =
                    asset = AssetState(tx.HashToByteString(),tx.AssetType, tx.Name, tx.Amount,
                                       Fixed8(0),tx.Precision, Fixed8(0), Fixed8(0), bytearray(20),
                                       tx.Owner, tx.Admin, tx.Admin, block.Index + 2 * 2000000, False )

                    assets.Add(tx.HashToByteString(), asset)

                elif tx.Type == int.from_bytes( TransactionType.IssueTransaction, 'little'):

                    txresults = [result for result in tx.GetTransactionResults() if result.Amount.value < 0]
                    for result in txresults:
                        asset = assets.GetAndChange(result.AssetId)
                        asset.Available = asset.Available.value - result.Amount.value


                elif tx.Type == int.from_bytes( TransactionType.ClaimTransaction, 'little'):

                    for input in tx.Claims:

                        sc = spentcoins.TryGet(input.PrevHash)
                        if sc and input.PrevIndex in sc.Items:
                            del sc.Items[input.PrevIndex]
                            spentcoins.GetAndChange(input.PrevHash)

                elif tx.Type == int.from_bytes( TransactionType.EnrollmentTransaction, 'little'):
                    validators.GetAndChange(tx.PublicKey, ValidatorState(pub_key=tx.PublicKey))

                elif tx.Type == int.from_bytes( TransactionType.PublishTransaction, 'little'):

                    contract = ContractState(tx.Code, tx.NeedStorage, tx.Name, tx.CodeVersion,
                                             tx.Author, tx.Email, tx.Description)

                    contracts.GetAndChange(tx.Code.ScriptHash(), contract)

                elif tx.Type == int.from_bytes( TransactionType.InvocationTransaction, 'little'):
                    # will have to create a VM / state machine first :-|
                    pass


            # do save all the accounts, unspent, coins, validators, assets, etc
            # now sawe the current sys block

            #filter out accounts to delete then commit
            for key,account in accounts.Collection.items():
                if not account.IsFrozen and len(account.Votes) == 0 and account.AllBalancesZeroOrLess():
                    accounts.Remove(key)
            accounts.Commit(wb)

            #filte out unspent coins to delete then commit
            for key, unspent in unspentcoins.Collection.items():
                unspentcoins.Remove(key)
            unspentcoins.Commit(wb)

            #filter out spent coins to delete then commit to db
            for key, spent in spentcoins.Collection.items():
                if len( spent.Items) == 0:
                    spentcoins.Remove(key)
            spentcoins.Commit(wb)

            #commit validators
            validators.Commit(wb)

            #commit assets
            assets.Commit(wb)

            #commit contracts
            contracts.Commit(wb)

            #commit storages ( not implemented )
            #storages.Commit(wb)


            sn.close()
            del sn

            contracts=None
            assets = None
            validators = None
            spentcoins = None
            unspentcoins = None
            accounts = None


            wb.put(DBPrefix.SYS_CurrentBlock, block.HashToByteString() + block.IndexBytes())
            self._current_block_height = block.Index
#            end = time.clock()
#            diff = end - start
#            self.__log.debug("Completed in %s " % diff)
#            self.__log.debug("_________________________________________")

#    @profile()
    def PersistBlocks(self):

#        self.__log.info("Header height, block height: %s/%s  --%s " % (self.Height(),self.HeaderHeight(), self.CurrentHeaderHash()))


        while not self._disposed:


            hash = None

            #lock header index
            if len(self._header_index) <= self._current_block_height + 1: break
            hash = self._header_index[self._current_block_height + 1]
            #end lock header index

#                self.__log.info("LOOKING FOR HASH: %s " % hash)
            block = None
            #lock block cache

            if not hash in self._block_cache:

#                if len(self._block_cache) > 20000:
#                    self.__log.debug("Resetting block cache :/")
#                    self._block_cache = {}
#                    self.SyncReset.on_change(hash)
                break

            block = self._block_cache[hash]

#                reactor.callFromThread(self.Persist,block)
#                reactor.callFromThread(self.OnPersistCompleted, block)
            self.Persist(block)
            self.OnPersistCompleted(block)

            #lock block cache
            del self._block_cache[hash]
            #end lock block cache


    def Dispose(self):
        self._disposed = True
        Blockchain.DeregisterBlockchain()
        self._header_index=[]
        self._db.close()
        closed = self._db.closed
        self._db = None
        return closed
