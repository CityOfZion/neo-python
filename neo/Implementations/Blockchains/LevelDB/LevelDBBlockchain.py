from neo.Core.Blockchain import Blockchain
from neo.Core.Header import Header
from enum import Enum
import plyvel
import ctypes
from ctypes import *
from autologging import logged
import pprint
import binascii

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

    _do_cache = False
    _verify_blocks = False

    def CurrentBlockHash(self):
        self.__log.debug("Getting Current bolck hash")
        return self._header_index[self._current_block_height]

    def CurrentHeaderHash(self):
        return self._header_index[self.HeaderHeight()]

    def HeaderHeight(self):
        height = len(self._header_index) - 1
        self.__log.debug("Getting Header height: %s " % height)
        return height

    def Height(self):
        return self._current_block_height

    def Path(self):
        return self._path

    def SetDoCache(self, val):
        self._do_cache = val

    def GetDoCache(self):
        return self._do_cache

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


        version = self._db.get_property(SYS_Version)
        self.__log.debug("current version %s " % version)

        self._current_block_height = self._db.get(SYS_CurrentBlock, 0)

        current_header_height = self._db.get(SYS_CurrentHeader, self._current_block_height)

        self.__log.debug("current header height, hashes %s %s " %(self._current_block_height, self._header_index) )

        hashes = []
        for key, value in self._db.iterator(start=IX_HeaderHashList):
            hashes.append({'index':key, 'hash':value})

        sorted(hashes, key=lambda i: i['index'])

        for h in hashes:
            if not h['hash'] == Blockchain.GenesisBlock().Hash():
                self._header_index.append(h['hash'])
            self._stored_header_count += 1

        if self._stored_header_count == 0:
            headers = []
            for key, value in self._db.iterator(start=DATA_Block):
                headers.append(  Header.FromTrimmedData(bytearray(value)[4:], 0))
            sorted(headers, key=lambda h: h.Index)

            for h in headers:
                self._header_index.append(h.HashToByteString())

#        elif current_header_height >= self._current_block_height:
#            current_hash = current_header_height
#            while not current_hash == self._header_index[self._stored_header_count -1]:
#                header = Header.FromTrimmedData( self._db.get(DATA_Block + hash), ctypes.sizeof(ctypes.c_long) )
#                self._header_index.insert(self._stored_header_count, current_hash)
#                current_hash = header.PrevHash


    def AddBlock(self, block):

        self.__log.debug("LEVELDB ADD BLOCK HEIGHT: %s  -- hash -- %s" % (block.Index, block.HashToByteString()))

        if self._do_cache:
            #lock block cache
            if not block.Hash() in self._block_cache:
                self._block_cache[block.Hash()] = block
            #end lock

        #lock header index
        header_len = len(self._header_index)
        if block.Index -1 >= header_len:
            self.__log.debug("Returning... block index -1 is greater than header length")
            return False

        if block.Index == header_len:
            self.__log.debug("Will try add block %s " % block.Index)

            if self._verify_blocks and not block.Verify():
                self.__log.debug("Block did not verify, will not add")
                return False

            #do some leveldb stuff here
            self.__log.debug("this is where we add the block to leveldb")

            if block.Index < header_len:
                #new_block_event.Set()
                #semaphore for therads or something
                pass

        #end lock header index

        return True

    def ContainsBlock(self,hash):

        self.__log.debug("checking if leveldb contains hash %s " % hash)

        header = self.GetHeader(hash)
        if header is not None and header.Index <= self._current_block_height:
            return True

        return False

    def GetHeader(self, hash):

        if self._do_cache:
            #lock header cache
            if hash in self._header_cache:
                return self._header_cache[hash]
            #end lock header cache

        self.__log.debug("get header from db not implementet yet")

        try:
            out = bytearray(self._db.get(DATA_Block + hash))[4:]
            outt = binascii.unhexlify(out)
            print("getting data from leveldb %s " % out)
            print("getting data from leveldb %s " % outt)

            self.__log.debug("heade hash from db out %s " % out)

            return Header.FromTrimmedData(outt, 0)
        except Exception as e:
            print("could not retrive header hash %s" % e)
        return None

    def GetHeaderByHeight(self, height):
        hash=None
        #lock header index
        if len(self._header_index) <= height: return False

        hash =  self._header_index[height]

        #endlock

        return self.GetHeader(hash)

    def GetBlockHash(self, height):
        if self._current_block_height < height: return False

        if len(self._header_index) <= height: return False

        return self._header_index[height]


    def AddHeader(self, header):
        self.AddHeaders( [ header])

    def AddHeaders(self, headers):
        print("adding headers!: %s " % headers[0].HashToByteString())

        self.__log.debug("Adding headers to LEVELDB: %s " % headers)
        # lock headers
        # lock header cache
        header_index_count = len(self._header_index)
        with self._db.write_batch() as wb:
            for header in headers:
                self.__log.debug('Writing header %s %s' % (header.Index, header.HashToByteString()))

                if header.Index - 1 >= header_index_count: break
                if header.Index < header_index_count: continue
                if self._verify_blocks and not header.Verify(): break


                if self._do_cache:
                    self._header_cache[header.HashToByteString()] = header

                self.OnAddHeader(header, wb)


        # unlock headers cache
        # unlock headers

    def OnAddHeader(self, header, wb):

        self.__log.debug("ON add header! %s " % header)

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

        self.__log.debug("Will try to add header to leveldb")
        print("adding to leveldb")
        print("will write raw data %s " % header.ToArray())
        wb.put( DATA_Block + hHash, bytes(4) + header.ToArray())
        wb.put( SYS_CurrentHeader,  hHash + header.Index.to_bytes( 4, 'little'))
        self.__log.debug("added header to leveldb!")
        print("added leveldb")

    def Persist(self, block):
        pass


    def Dispose(self):
        Blockchain.DeregisterBlockchain()
        self._header_index=[]
        self._db.close()
        closed = self._db.closed
        self._db = None
        return closed
