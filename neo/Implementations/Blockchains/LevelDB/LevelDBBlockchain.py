from neo.Core.Blockchain import Blockchain
from neo.Core.Header import Header
from neo.Core.TX.Transaction import Transaction,TransactionType,TransactionInput, TransactionOutput
import plyvel
from autologging import logged
import binascii
import asyncio
from concurrent.futures import ThreadPoolExecutor
import ctypes
import time
import threading

DATA_Block =        b'\x01'
DATA_Transaction =  b'\x02'

ST_Account =        b'\x40'
ST_Coin =           b'\x44'
ST_SpentCoin =      b'\x45'
ST_Validator =      b'\x48'
ST_Asset =          b'\x4c'
ST_Contract =       b'\x50'
ST_Storage =        b'\x70'

IX_HeaderHashList = b'\x80'

SYS_CurrentBlock =  b'\xc0'
SYS_CurrentHeader = b'\xc1'
SYS_Version =       b'\xf0'


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

    _sysversion = b'/NEO:2.0.1/'

    def CurrentBlockHash(self):
#        self.__log.debug("Getting Current bolck hash")
        return self._header_index[self._current_block_height]

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
 #       self.__log.debug("Getting Header height: %s " % height)
        return height

    def Height(self):
        return self._current_block_height

    def Path(self):
        return self._path


    def __init__(self, path):
        super(LevelDBBlockchain,self).__init__()
        self._path = path
        self.__log.debug('Initialized LEVELDB')

        self._header_index = []
        self._header_index.append(Blockchain.GenesisBlock().Header().HashToByteString())

        try:
            self._db = plyvel.DB(self._path, create_if_missing=True)
        except Exception as e:
            print("leveldb unavailable, you may already be running this process: %s " % e)
            raise Exception('Leveldb Unavailable')


        version = self._db.get(SYS_Version)
        print("version %s " % version)
        if version == self._sysversion: #or in the future, if version doesn't equal the current version...
            self.__log.debug("current version %s " % version)

            ba=bytearray(self._db.get(SYS_CurrentBlock))
            self._current_block_height = int.from_bytes( ba[-4:], 'little')


            ba = bytearray(self._db.get(SYS_CurrentHeader))
            current_header_height = int.from_bytes(ba[-4:], 'little')

            print("current header height, hashes %s %s %s" %(self._current_block_height, self._header_index, current_header_height) )

#            hashes = []
#            for key, value in self._db.iterator(prefix=DATA_Block):
#                hashes.append({'index':key, 'hash':value})

 #           print("hashes: %s " % len(hashes) )
 #           sorted(hashes, key=lambda i: i['index'])

#            for h in hashes:
#                if not h['hash'] == Blockchain.GenesisBlock().Hash():
#                    self._header_index.append(h['hash'])
#                self._stored_header_count += 1
#            print("hashes: %s " % hashes, self._stored_header_count)

            if self._stored_header_count == 0:
                headers = []
                for key, value in self._db.iterator(prefix=DATA_Block):
                    dbhash = bytearray(value)[4:]
                    headers.append(  Header.FromTrimmedData(binascii.unhexlify(dbhash), 0))

                headers.sort(key=lambda h: h.Index)
                for h in headers:
                    self._header_index.append(h.HashToByteString())

#            elif current_header_height >= self._current_block_height:
#                current_hash = current_header_height
#                while not current_hash == self._header_index[self._stored_header_count -1]:
#                    dbhash = bytearray(self._db.get(DATA_Block + current_hash))[4:]
#                    header = Header.FromTrimmedData( binascii.unhexlify(dbhash), 0)
#                    self._header_index.insert(self._stored_header_count, current_hash)
#                    current_hash = header.PrevHash

        else:
            with self._db.write_batch() as wb:
                for key,value in self._db.iterator():
                    wb.delete(key)

            self.Persist(Blockchain.GenesisBlock())
            self._db.put(SYS_Version, self._sysversion )

        #start a thread for persisting blocks
        #we dont want to do this during testing
        if self._path != './UnitTestChain':
            try:
                t = threading.Thread(target=self.PersistBlocks)
                t.daemon=True
                t.start()
            except Exception as e:
                print("exception running persist blocks therad %s " % e)


    def AddBlock(self, block):

#        self.__log.debug("LEVELDB ADD BLOCK HEIGHT: %s  -- hash -- %s -- %s" % (block.Index, self._current_block_height, block.HashToByteString()))

        #lock block cache
        if not block.HashToByteString() in self._block_cache:
#            print("adding block to block cache %s " % len(self._block_cache))
            self._block_cache[block.HashToByteString()] = block
        #end lock

        #lock header index
        header_len = len(self._header_index)
        if block.Index -1 >= header_len:
#            self.__log.debug("Returning... block index -1 is greater than header length %s %s %s" % (block.Index, header_len, self._current_block_height))
            return False

        if block.Index == header_len:
#            self.__log.debug("Will try add block %s " % block.Index)

            if self._verify_blocks and not block.Verify():
#                self.__log.debug("Block did not verify, will not add")
                return False

            #do some leveldb stuff here
#            self.__log.debug("this is where we add the block to leveldb")

            self.AddHeader(block.Header())

            if block.Index < header_len:
                #new_block_event.Set()
                #semaphore for therads or something
                pass

        #end lock header index

        return True

    def ContainsBlock(self,hash):

        header = self.GetHeader(hash)
        if header is not None and header.Index <= self._current_block_height:
            return True

        return False

    def GetHeader(self, hash):

        #lock header cache
        if hash in self._header_cache:
            return self._header_cache[hash]
        #end lock header cache

#        self.__log.debug("get header from db not implementet yet")

        try:
            out = bytearray(self._db.get(DATA_Block + hash))
            out = out[4:]
            outhex = binascii.unhexlify(out)
            return Header.FromTrimmedData(outhex, 0)
        except TypeError:
            print("hash not found")
        except Exception as e:
            print("OTHER ERRROR %s " % e)
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
        return 0


    def AddHeader(self, header):
        self.AddHeaders( [ header])

    def AddHeaders(self, headers):

        self.__log.debug("Adding headers to LEVELDB: ...  " )
        # lock headers
        # lock header cache
        with self._db.write_batch() as wb:
            for header in headers:

                if header.Index - 1 >= len(self._header_index): break
                if header.Index < len(self._header_index): continue
                if self._verify_blocks and not header.Verify(): break


                self._header_cache[header.HashToByteString()] = header

                self.OnAddHeader(header, wb)


        # unlock headers cache
        # unlock headers

    def OnAddHeader(self, header, wb):


        hHash = header.HashToByteString()

        if not hHash in self._header_index:

            self._header_index.append(hHash)

#clean up old headers?
#        while header.Index - 2000 >= self._stored_header_count:
#            ms = MemoryStream()
#            w = BinaryWriter(ms)
#            w.Write(header_index.Skip((int)stored_header_count).Take(2000).ToArray());
#            w.Flush()
#            batch.Put(SliceBuilder.Begin(DataEntryPrefix.IX_HeaderHashList).Add(stored_header_count), ms.ToArray());
#            stored_header_count += 2000;

        wb.put( DATA_Block + hHash, bytes(4) + header.ToArray())
        wb.put( SYS_CurrentHeader,  hHash + header.Index.to_bytes( 4, 'little'))

    def Persist(self, block):

        self.__log.debug("________________________________")
        self.__log.debug("________________________________")
        self.__log.debug("PERSISTING BLOCK %s " % block.Index)
        self.__log.debug("Total Headers %s " % self.HeaderHeight())
        self.__log.debug("________________________________")
        self.__log.debug("________________________________")

        sn = self._db.snapshot()

        accounts = sn.iterator(prefix=ST_Account)
        unspentcoins = sn.iterator(prefix=ST_Coin)
        spentcoins = sn.iterator(prefix=ST_SpentCoin)
        validators = sn.iterator(prefix=ST_Validator)
        assets = sn.iterator(prefix=ST_Asset)
        contracts = sn.iterator(prefix=ST_Contract)
        storages = sn.iterator(prefix=ST_Storage)

        amount_sysfee = (self.GetSysFeeAmount(block.PrevHash) + block.TotalFees()).to_bytes(4, 'little')

        with self._db.write_batch() as wb:

            wb.put(DATA_Block + block.HashToByteString(), amount_sysfee + block.Trim())

            for tx in block.Transactions:

                wb.put(DATA_Transaction + tx.HashToByteString(), block.IndexBytes() + tx.ToArray())

                #do a whole lotta stuff with tx here...
                if tx.Type == TransactionType.RegisterTransaction:
                    pass

                elif tx.Type == TransactionType.IssueTransaction:
                    pass

                elif tx.Type == TransactionType.IssueTransaction:
                    pass

                elif tx.Type == TransactionType.ClaimTransaction:
                    pass

                elif tx.Type == TransactionType.EnrollmentTransaction:
                    pass

                elif tx.Type == TransactionType.PublishTransaction:
                    pass
                elif tx.Type == TransactionType.InvocationTransaction:
                    pass

            #do save all the accounts, unspent, coins, validators, assets, etc
            #now sawe the current sys block
            wb.put(SYS_CurrentBlock, block.HashToByteString() + block.IndexBytes())
            self._current_block_height = block.Index


    def PersistBlocks(self):

        while not self._disposed:



            time.sleep(1)
#            self.__log.debug("Header height, block height: %s %s %s " % (self.HeaderHeight(), self.Height(), self.CurrentHeaderHash()))
            while not self._disposed:
                hash = None

                #lock header index
                if len(self._header_index) <= self._current_block_height + 1: break
#                self.__log.debug("should add block at index %s " % (self._current_block_height + 1))
                hash = self._header_index[self._current_block_height + 1]
                #end lock header index

#                self.__log.debug("LOOKING FOR HASH: %s " % hash)
                block = None
                #lock block cache

                if not hash in self._block_cache:
#                    self.__log.debug("hash not in block cache!!!")
#                    self.__log.debug("CURRENT BLOCK CACHE %s " % (len(self._block_cache)))
                    break

                block = self._block_cache[hash]
#                self.__log.debug("block is in block cache, persist!! %s "% block)
                #end lock block cache

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
