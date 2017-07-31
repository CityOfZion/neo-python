from neo.Core.Blockchain import Blockchain
from neo.Core.Header import Header
from enum import Enum
import plyvel
import ctypes
from ctypes import *


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

class LevelDBBlockchain(Blockchain):

    _db = None
    _thread = None
    _header_index = []
    _header_cache = {}
    _block_cache = {}
    _current_block_height = 0
    _stored_header_count = 0

    _disposed = False

    _verify_blocks = False

    def CurrentBlockHash(self):
        return self._header_index[self._current_block_height]

    def CurrentHeaderHash(self):
        return self._header_index[self.HeaderHeight()]

    def HeaderHeight(self):
        print("getting header height leveldb")
        return len(self._header_index) - 1

    def Height(self):
        return self._current_block_height


    def __init__(self, path):
        super(LevelDBBlockchain,self).__init__()

        self._header_index.append(Blockchain.GenesisBlock())

        try:
            self._db = plyvel.DB(path, create_if_missing=True)
        except Exception as e:
            print("leveldb unavailable, you may already be running this process: %s " % e)


        print("type: %s " % type(SYS_Version))
        version = self._db.get_property(SYS_Version)
        print("version: %s " % version)

#        self._current_block_height = self._db.get(SYS_CurrentBlock, 0, False)
        self._current_block_height = self._db.get(SYS_CurrentBlock, 0)

        current_header_height = self._db.get(SYS_CurrentHeader, self._current_block_height)

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
                headers.append(  Header.FromTrimmedData(value, key))
            sorted(headers, key=lambda h: h.Index)

            for h in headers:
                self._header_index.append(h.Hash())

        elif current_header_height >= self._current_block_height:
            current_hash = current_header_height
            while not current_hash == self._header_index[self._stored_header_count -1]:
                header = Header.FromTrimmedData( self._db.get(DATA_Block + hash), ctypes.sizeof(ctypes.c_long) )
                self._header_index.insert(self._stored_header_count, current_hash)
                current_hash = header.PrevHash


    def AddBlock(self, block):

        print("LEVELDB ADD BLOCK %s " % block)
        header_len = len(self._header_index)
        if block.Index -1 >= header_len:
            return False

        if block.Index == header_len:
            if self._verify_blocks and not block.Verify(): return False

        print("add block not fully implemented ....")

    def ContainsBlock(self,hash):
        print("checking if leveldb contains hash %s " % hash)
        print("return false for now")
        return False