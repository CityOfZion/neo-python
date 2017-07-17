from neo.Core.Blockchain import Blockchain
from neo.Core.Header import Header
from enum import Enum
import plyvel
import ctypes
from ctypes import *

class DataEntryPrefix(Enum):

    DATA_Block =        b'0x01'
    DATA_Transaction =  b'0x02'

    ST_Account =        b'0x40'
    ST_Coin =           b'0x44'
    ST_SpentCoin =      b'0x45'
    ST_Validator =      b'0x48'
    ST_Asset =          b'0x4c'
    ST_Contract =       b'0x50'
    ST_Storage =        b'0x70'

    IX_HeaderHashList = b'0x80'

    SYS_CurrentBlock =  b'0xc0'
    SYS_CurrentHeader = b'0xc1'
    SYS_Version =       b'0xf0'

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
        return len(self._header_index) - 1

    def Height(self):
        return self._current_block_height


    def __init__(self, path):
        super(LevelDBBlockchain,self).__init__()

        self._header_index.append(Blockchain.GenesisBlock())

        self._db = plyvel.DB(path, create_if_missing=True)

        version = self._db.get_property(DataEntryPrefix.SYS_Version)
        print("version: %s " % version)

        self._current_block_height = self._db.get(DataEntryPrefix.SYS_CurrentBlock, 0, False)

        current_header_height = self._db.get(DataEntryPrefix.SYS_CurrentHeader, self._current_block_height, False)

        hashes = []
        for key, value in self._db.iterator(DataEntryPrefix.IX_HeaderHashList):
            hashes.append({'index':key, 'hash':value})

        sorted(hashes, key=lambda i: i['index'])

        for h in hashes:
            if not h['hash'] == Blockchain.GenesisBlock().Hash():
                self._header_index.append(h['hash'])
            self._stored_header_count += 1

        if self._stored_header_count == 0:
            headers = []
            for key, value in self._db.iterator(DataEntryPrefix.DATA_Block):
                headers.append(  Header.FromTrimmedData(value, key))
            sorted(headers, key=lambda h: h.Index)

            for h in headers:
                self._header_index.append(h.Hash())

        elif current_header_height >= self._current_block_height:
            current_hash = current_header_height
            while not current_hash == self._header_index[self._stored_header_count -1]:
                header = Header.FromTrimmedData( self._db.get(DataEntryPrefix.DATA_Block + hash), ctypes.sizeof(ctypes.c_long) )
                self._header_index.insert(self._stored_header_count, current_hash)
                current_hash = header.PrevHash


    def AddBlock(self, block):
        header_len = len(self._header_index)
        if block.Index -1 >= header_len:
            return False

        if block.Index == header_len:
            if self._verify_blocks and not block.Verify(): return False
