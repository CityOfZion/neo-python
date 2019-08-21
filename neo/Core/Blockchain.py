import pytz
import asyncio
import binascii
import struct
import traceback
import os
import json
from neo.VM.VMState import VMStateStr
from contextlib import suppress
from neo.VM import InteropService

from itertools import groupby
from datetime import datetime
from neo.Storage.Common.DataCache import TrackState

from neo.Network.common import Events
import neo.Core.Block
from neo.Core.TX.Transaction import TransactionOutput
from neo.Core.AssetType import AssetType
from neo.Core.Cryptography.Crypto import Crypto
from neo.Core.Header import Header
from neo.Core.TX.RegisterTransaction import RegisterTransaction
from neo.Core.TX.MinerTransaction import MinerTransaction
from neo.Core.TX.IssueTransaction import IssueTransaction
from neo.Core.TX.Transaction import Transaction, TransactionType
from neo.Core.Witness import Witness
from neo.Core.State.UnspentCoinState import UnspentCoinState
from neo.Core.State.AccountState import AccountState
from neo.Core.State.CoinState import CoinState
from neo.Core.State.ContractState import ContractState
from neo.Core.State.StorageItem import StorageItem
from neo.Core.State.SpentCoinState import SpentCoinState, SpentCoinItem, SpentCoin
from neo.Core.State.AssetState import AssetState
from neo.Core.State.ValidatorState import ValidatorState
from neo.Core.IO.BinaryReader import BinaryReader
from neo.IO.MemoryStream import StreamManager
from neo.logging import log_manager
from neo.Settings import settings
from neo.Core.Fixed8 import Fixed8
from neo.Core.Cryptography.ECCurve import ECDSA
from neo.Core.UInt256 import UInt256
from neo.Core.UInt160 import UInt160
from neo.Core.IO.BinaryWriter import BinaryWriter

from neo.SmartContract.StateMachine import StateMachine
from neo.SmartContract.Contract import Contract
from neo.SmartContract.ApplicationEngine import ApplicationEngine
from neo.Storage.Common.DBPrefix import DBPrefix
from neo.Storage.Common.CachedScriptTable import CachedScriptTable
from neo.Storage.Interface.DBInterface import DBInterface
from neo.Storage.Interface.DBProperties import DBProperties
from neo.SmartContract import TriggerType
from neo.VM.OpCode import PUSHF, PUSHT
from functools import lru_cache
from neo.Network.common import msgrouter
from neo.EventHub import events

from neo.Network.common import blocking_prompt as prompt
from neo.Network.common import wait_for
from typing import Tuple

import neo.Storage.Implementation.DBFactory as DBFactory

logger = log_manager.getLogger()


class Blockchain:
    SECONDS_PER_BLOCK = 15

    DECREMENT_INTERVAL = 2000000

    GENERATION_AMOUNT = [8, 7, 6, 5, 4, 3, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

    _db = None

    _blockchain = None

    _validators = []

    _genesis_block = None

    _instance = None

    _blockrequests = set()

    _paused = False

    _disposed = False

    _verify_blocks = False

    _header_index = []

    _block_cache = {}

    _current_block_height = 0
    _stored_header_count = 0

    _persisting_block = None

    TXProcessed = 0

    BlockSearchTries = 0

    _sysversion = b'schema v.0.8.5'

    CACHELIM = 4000
    CMISSLIM = 5
    LOOPTIME = .1

    PersistCompleted = Events()

    Notify = Events()

    # debug:
    _previous_blockid = None

    def __init__(self, db, skip_version_check=False, skip_header_check=False):
        self._db = db
        self._header_index = []

        self._header_index.append(Blockchain.GenesisBlock().Header.Hash.ToBytes())

        self.TXProcessed = 0
        version = self._db.get(DBPrefix.SYS_Version)

        if skip_version_check:
            self._db.write(DBPrefix.SYS_Version, self._sysversion)
            version = self._sysversion

        if version == self._sysversion:  # or in the future, if version doesn't equal the current version...
            ba = bytearray(self._db.get(DBPrefix.SYS_CurrentBlock, 0))
            self._current_block_height = int.from_bytes(ba[-4:], 'little')

            if not skip_header_check:
                ba = bytearray(self._db.get(DBPrefix.SYS_CurrentHeader, 0))
                current_header_height = int.from_bytes(ba[-4:], 'little')
                current_header_hash = bytes(ba[:64].decode('utf-8'), encoding='utf-8')

                hashes = []
                try:
                    with self._db.openIter(DBProperties(DBPrefix.IX_HeaderHashList)) as it:
                        for key, value in it:
                            ms = StreamManager.GetStream(value)
                            reader = BinaryReader(ms)
                            hlist = reader.Read2000256List()
                            key = int.from_bytes(key[-4:], 'little')
                            hashes.append({'k': key, 'v': hlist})
                            StreamManager.ReleaseStream(ms)
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
                    logger.info("Current stored headers empty, re-creating from stored blocks...")
                    headers = []
                    logger.info('Recreate headers')
                    with self._db.openIter(DBProperties(DBPrefix.DATA_Block)) as it:
                        for key, value in it:
                            dbhash = bytearray(value)[8:]
                            headers.append(Header.FromTrimmedData(binascii.unhexlify(dbhash), 0))

                    headers.sort(key=lambda h: h.Index)
                    for h in headers:
                        if h.Index > 0:
                            self._header_index.append(h.Hash.ToBytes())

                    if len(headers):
                        self.OnAddHeader(headers[-1])

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

        elif version is None:
            wait_for(self.Persist(Blockchain.GenesisBlock()))
            self._db.write(DBPrefix.SYS_Version, self._sysversion)
        else:
            logger.error("\n\n")
            logger.warning("Database schema has changed from %s to %s.\n" % (version, self._sysversion))
            logger.warning("You must either resync from scratch, or use the np-bootstrap command to bootstrap the chain.")

            res = prompt("Type 'continue' to erase your current database and sync from new. Otherwise this program will exit:\n> ")
            if res == 'continue':

                with self._db.getBatch() as wb:
                    with self._db.openIter(DBProperties(include_value=False)) as it:
                        for key in it:
                            wb.delete(key)

                wait_for(self.Persist(Blockchain.GenesisBlock()))
                self._db.write(DBPrefix.SYS_Version, self._sysversion)

            else:
                raise Exception("Database schema changed")

    @staticmethod
    def StandbyValidators():
        if len(Blockchain._validators) < 1:
            vlist = settings.STANDBY_VALIDATORS
            for pkey in settings.STANDBY_VALIDATORS:
                Blockchain._validators.append(ECDSA.decode_secp256r1(pkey).G)

        return Blockchain._validators

    @staticmethod
    @lru_cache(maxsize=2)
    def SystemShare():
        """
        Register AntShare.

        Returns:
            RegisterTransaction:
        """
        amount = Fixed8.FromDecimal(sum(Blockchain.GENERATION_AMOUNT) * Blockchain.DECREMENT_INTERVAL)
        owner = ECDSA.secp256r1().Curve.Infinity
        admin = Crypto.ToScriptHash(PUSHT)
        return RegisterTransaction([], [], AssetType.GoverningToken,
                                   "[{\"lang\":\"zh-CN\",\"name\":\"小蚁股\"},{\"lang\":\"en\",\"name\":\"AntShare\"}]",
                                   amount, 0, owner, admin)

    @staticmethod
    @lru_cache(maxsize=2)
    def SystemCoin():
        """
        Register AntCoin

        Returns:
            RegisterTransaction:
        """
        amount = Fixed8.FromDecimal(sum(Blockchain.GENERATION_AMOUNT) * Blockchain.DECREMENT_INTERVAL)

        owner = ECDSA.secp256r1().Curve.Infinity

        precision = 8
        admin = Crypto.ToScriptHash(PUSHF)

        return RegisterTransaction([], [], AssetType.UtilityToken,
                                   "[{\"lang\":\"zh-CN\",\"name\":\"小蚁币\"},{\"lang\":\"en\",\"name\":\"AntCoin\"}]",
                                   amount, precision, owner, admin)

    @staticmethod
    def GenesisBlock():
        """
        Create the GenesisBlock.

        Returns:
            BLock:
        """
        prev_hash = UInt256(data=bytearray(32))
        timestamp = int(datetime(2016, 7, 15, 15, 8, 21, tzinfo=pytz.utc).timestamp())
        index = 0
        consensus_data = 2083236893  # Pay tribute To Bitcoin
        next_consensus = Blockchain.GetConsensusAddress(Blockchain.StandbyValidators())
        script = Witness(bytearray(0), bytearray(PUSHT))

        mt = MinerTransaction()
        mt.Nonce = 2083236893

        output = TransactionOutput(
            Blockchain.SystemShare().Hash,
            Blockchain.SystemShare().Amount,
            Crypto.ToScriptHash(
                Contract.CreateMultiSigRedeemScript(
                    int(len(Blockchain.StandbyValidators()) / 2) + 1,
                    Blockchain.StandbyValidators()
                )
            )
        )

        it = IssueTransaction([], [output], [], [script])

        return neo.Core.Block.Block(prev_hash, timestamp, index, consensus_data, next_consensus, script,
                                    [mt, Blockchain.SystemShare(), Blockchain.SystemCoin(), it], True)

    def GetDB(self):
        if self._db is not None:
            return self._db
        raise ('Database not defined')

    @staticmethod
    def Default() -> 'Blockchain':
        """
        Get the default registered blockchain instance.

        Returns:
            obj: Blockchain based on the configured database backend.
        """
        if Blockchain._instance is None:
            Blockchain._instance = Blockchain(DBFactory.getBlockchainDB())
            Blockchain.GenesisBlock().RebuildMerkleRoot()

        return Blockchain._instance

    @property
    def CurrentBlockHash(self):
        try:
            return self._header_index[self._current_block_height]
        except Exception as e:
            logger.info("Could not get current block hash, returning none: %s ", e)

        return None

    @property
    def CurrentHeaderHash(self):
        return self._header_index[-1]

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

    def AddBlock(self, block):
        if not block.Hash.ToBytes() in self._block_cache:
            self._block_cache[block.Hash.ToBytes()] = block

        header_len = len(self._header_index)

        if block.Index - 1 >= header_len:
            return False

        if block.Index == header_len:

            if self._verify_blocks and not block.Verify():
                return False
            elif len(block.Transactions) < 1:
                return False
            self.AddHeader(block.Header)

        return True

    def AddBlockDirectly(self, block, do_persist_complete=True):
        # Adds a block when importing, which skips adding
        # the block header
        if block.Index != self.Height + 1:
            raise Exception("Invalid block")
        self.Persist(block)
        if do_persist_complete:
            self.OnPersistCompleted(block)

    def AddHeader(self, header):
        return self.AddHeaders([header])

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

        return count

    def ProcessNewHeaders(self, headers):
        lastheader = headers[-1]
        hashes = [h.Hash.ToBytes() for h in headers]
        self._header_index.extend(hashes)

        if lastheader is not None:
            self.OnAddHeader(lastheader)

    def OnAddHeader(self, header):

        hHash = header.Hash.ToBytes()

        with self._db.getBatch() as wb:
            while header.Index - 2000 >= self._stored_header_count:
                ms = StreamManager.GetStream()
                w = BinaryWriter(ms)
                headers_to_write = self._header_index[self._stored_header_count:self._stored_header_count + 2000]
                w.Write2000256List(headers_to_write)
                out = ms.ToArray()
                StreamManager.ReleaseStream(ms)
                wb.put(DBPrefix.IX_HeaderHashList + self._stored_header_count.to_bytes(4, 'little'), out)

                self._stored_header_count += 2000

            if self._db.get(DBPrefix.DATA_Block + hHash) is None:
                wb.put(DBPrefix.DATA_Block + hHash, bytes(8) + header.ToArray())
            wb.put(DBPrefix.SYS_CurrentHeader, hHash + header.Index.to_bytes(4, 'little'))

    @property
    def BlockRequests(self):
        """
        Outstanding block requests.

        Returns:
            set:
        """
        return self._blockrequests

    def ResetBlockRequests(self):
        self._blockrequests = set()

    @staticmethod
    def CalculateBonusIgnoreClaimed(inputs, ignore_claimed=True):
        unclaimed = []

        for hash, group in groupby(inputs, lambda x: x.PrevHash):
            claimable = Blockchain.Default().GetUnclaimed(hash)
            if claimable is None or len(claimable) < 1:
                if ignore_claimed:
                    continue
                else:
                    raise Exception("Error calculating bonus without ignoring claimed")

            for coinref in group:
                if coinref.PrevIndex in claimable:
                    claimed = claimable[coinref.PrevIndex]
                    unclaimed.append(claimed)
                else:
                    if ignore_claimed:
                        continue
                    else:
                        raise Exception("Error calculating bonus without ignoring claimed")

        return Blockchain.CalculateBonusInternal(unclaimed)

    @staticmethod
    def CalculateBonus(inputs, height_end):
        unclaimed = []

        for hash, group in groupby(inputs, lambda x: x.PrevHash):
            tx, height_start = Blockchain.Default().GetTransaction(hash)

            if tx is None:
                raise Exception("Could Not calculate bonus")

            if height_start == height_end:
                continue

            for coinref in group:
                if coinref.PrevIndex >= len(tx.outputs) or tx.outputs[coinref.PrevIndex].AssetId != Blockchain.SystemShare().Hash:
                    raise Exception("Invalid coin reference")
                spent_coin = SpentCoin(output=tx.outputs[coinref.PrevIndex], start_height=height_start,
                                       end_height=height_end)
                unclaimed.append(spent_coin)

        return Blockchain.CalculateBonusInternal(unclaimed)

    @staticmethod
    def CalculateBonusInternal(unclaimed):
        amount_claimed = Fixed8.Zero()

        decInterval = Blockchain.DECREMENT_INTERVAL
        genAmount = Blockchain.GENERATION_AMOUNT
        genLen = len(genAmount)

        for coinheight, group in groupby(unclaimed, lambda x: x.Heights):
            amount = 0
            ustart = int(coinheight.start / decInterval)

            if ustart < genLen:

                istart = coinheight.start % decInterval
                uend = int(coinheight.end / decInterval)
                iend = coinheight.end % decInterval

                if uend >= genLen:
                    iend = 0

                if iend == 0:
                    uend -= 1
                    iend = decInterval

                while ustart < uend:
                    amount += (decInterval - istart) * genAmount[ustart]
                    ustart += 1
                    istart = 0

                amount += (iend - istart) * genAmount[ustart]

            endamount = Blockchain.Default().GetSysFeeAmountByHeight(coinheight.end - 1)
            startamount = 0 if coinheight.start == 0 else Blockchain.Default().GetSysFeeAmountByHeight(
                coinheight.start - 1)
            amount += endamount - startamount

            outputSum = 0

            for spentcoin in group:
                outputSum += spentcoin.Value.value

            outputSum = outputSum / 100000000
            outputSumFixed8 = Fixed8(int(outputSum * amount))
            amount_claimed += outputSumFixed8

        return amount_claimed

    def OnNotify(self, notification):
        self.Notify.on_change(notification)

    def ContainsBlock(self, index):
        if index <= self._current_block_height:
            return True
        return False

    def ContainsTransaction(self, hash):
        tx = self._db.get(DBPrefix.DATA_Transaction + hash.ToBytes())
        return True if tx is not None else False

    def GetHeader(self, hash):
        if isinstance(hash, UInt256):
            hash = hash.ToString().encode()

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

        if intval is None and len(height_or_hash) == 64:
            bhash = height_or_hash.encode('utf-8')
            if bhash in self._header_index:
                hash = bhash

        elif intval is None and len(height_or_hash) == 66:
            bhash = height_or_hash[2:].encode('utf-8')
            if bhash in self._header_index:
                hash = bhash

        elif intval is not None and self.GetHeaderHash(intval) is not None:
            hash = self.GetHeaderHash(intval)

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
            bytes: a non-raw block hash (e.g. b'6dd83ed8a3fc02e322f91f30431bf3662a8c8e8ebe976c3565f0d21c70620991', but not b'\x6d\xd8...etc'
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
            amount = struct.unpack("<d", value)[0]
            return amount
        except Exception as e:
            logger.debug("Could not get sys fee: %s " % e)

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
            if isinstance(height_or_hash, str):
                bhash = height_or_hash.encode('utf-8')
            else:
                bhash = height_or_hash

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
            return neo.Core.Block.Block.FromTrimmedData(outhex)
        except Exception as e:
            logger.info("Could not get block %s " % e)
        return None

    def GetStates(self, prefix, classref):
        return DBInterface(self._db, prefix, classref)

    def GetAccountState(self, address, print_all_accounts=False):

        if type(address) is str:
            try:
                address = address.encode('utf-8')
            except Exception as e:
                logger.info("could not convert argument to bytes :%s " % e)
                return None

        accounts = DBInterface(self._db, DBPrefix.ST_Account, AccountState)
        acct = accounts.TryGet(keyval=address)

        return acct

    def GetStorageItem(self, storage_key):
        storages = DBInterface(self._db, DBPrefix.ST_Storage, StorageItem)
        item = storages.TryGet(storage_key.ToArray())
        return item

    def GetAssetState(self, assetId):
        if type(assetId) is str:
            try:
                assetId = assetId.encode('utf-8')
            except Exception as e:
                logger.info("could not convert argument to bytes :%s " % e)
                return None

        assets = DBInterface(self._db, DBPrefix.ST_Asset, AssetState)
        asset = assets.TryGet(assetId)

        return asset

    def ShowAllAssets(self):
        res = []
        with self._db.openIter(DBProperties(DBPrefix.ST_Asset, include_value=False)) as it:
            for key in it:
                res.append(key[1:])  # remove prefix byte

        return res

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
        return None, -1

    def SearchContracts(self, query):
        res = []

        snapshot = self._db.createSnapshot()
        keys = []
        with self._db.openIter(DBProperties(DBPrefix.ST_Contract, include_value=False)) as it:
            for key in it:
                keys.append(key[1:])  # remove prefix byte

        query = query.casefold()

        for item in keys:

            contract = snapshot.Contracts.TryGet(item)
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

        return res

    def ShowAllContracts(self):

        keys = []
        with self._db.openIter(DBProperties(DBPrefix.ST_Contract, include_value=False)) as it:
            for key in it:
                keys.append(key[1:])  # remove prefix byte

        return keys

    def GetContract(self, hash):

        if type(hash) is str:
            try:
                hash = UInt160.ParseString(hash).ToBytes()
            except Exception as e:
                logger.info("could not convert argument to bytes :%s " % e)
                return None

        contracts = DBInterface(self._db, DBPrefix.ST_Contract, ContractState)
        contract = contracts.TryGet(keyval=hash)
        return contract

    def GetAllSpentCoins(self):
        coins = DBInterface(self._db, DBPrefix.ST_SpentCoin, SpentCoinState)

        return coins.Keys

    def GetUnspent(self, hash, index):

        coins = DBInterface(self._db, DBPrefix.ST_Coin, UnspentCoinState)

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

        coins = DBInterface(self._db, DBPrefix.ST_SpentCoin, SpentCoinState)
        result = coins.TryGet(keyval=tx_hash)

        return result

    def GetAllUnspent(self, hash):

        unspents = []

        unspentcoins = DBInterface(self._db, DBPrefix.ST_Coin, UnspentCoinState)

        state = unspentcoins.TryGet(keyval=hash.ToBytes())

        if state:
            tx, height = self.GetTransaction(hash)

            for index, item in enumerate(state.Items):
                if item & CoinState.Spent == 0:
                    unspents.append(tx.outputs[index])
        return unspents

    def GetUnclaimed(self, hash):

        tx, height = self.GetTransaction(hash)

        if tx is None:
            return None

        out = {}
        coins = DBInterface(self._db, DBPrefix.ST_SpentCoin, SpentCoinState)

        state = coins.TryGet(keyval=hash.ToBytes())

        if state:
            for item in state.Items:
                out[item.index] = SpentCoin(tx.outputs[item.index], height, item.height)

        return out

    def SearchAssetState(self, query):
        res = []

        snapshot = self._db.createSnapshot()
        keys = []
        with self._db.openIter(DBProperties(DBPrefix.ST_Asset, include_value=False)) as it:
            for key in it:
                keys.append(key[1:])  # remove prefix byte

        if query.lower() == "neo":
            query = "AntShare"

        if query.lower() in {"gas", "neogas"}:
            query = "AntCoin"

        for item in keys:
            asset = snapshot.Assets.TryGet(item)
            if query in asset.Name.decode('utf-8'):
                res.append(asset)
            elif query in Crypto.ToAddress(asset.Issuer):
                res.append(asset)
            elif query in Crypto.ToAddress(asset.Admin):
                res.append(asset)

        return res

    def GetEnrollments(self):
        # abstract
        pass

    @staticmethod
    def GetConsensusAddress(validators):
        """
        Get the script hash of the consensus node.

        Args:
            validators (list): of Ellipticcurve.ECPoint's

        Returns:
            UInt160:
        """
        vlen = len(validators)
        script = Contract.CreateMultiSigRedeemScript(vlen - int((vlen - 1) / 3), validators)
        return Crypto.ToScriptHash(script)

    def GetValidators(self, others):

        # votes = Counter([len(vs.PublicKeys) for vs in self.GetVotes(others)]).items()
        # TODO: Sorting here may cost a lot of memory, considering whether to use other mechanisms
        #           votes = GetVotes(others).OrderBy(p => p.PublicKeys.Length).ToArray()
        #            int validators_count = (int)votes.WeightedFilter(0.25, 0.75, p => p.Count.GetData(), (p, w) => new
        #            {
        #                ValidatorsCount = p.PublicKeys.Length,
        #                Weight = w
        #            }).WeightedAverage(p => p.ValidatorsCount, p => p.Weight)
        #            validators_count = Math.Max(validators_count, StandbyValidators.Length)
        #            Dictionary<ECPoint, Fixed8> validators = GetEnrollments().ToDictionary(p => p.PublicKey, p => Fixed8.Zero)
        #            foreach (var vote in votes)
        #            {
        #                foreach (ECPoint pubkey in vote.PublicKeys.Take(validators_count))
        #                {
        #                    if (validators.ContainsKey(pubkey))
        #                        validators[pubkey] += vote.Count
        #                }
        #            }
        #            return validators.OrderByDescending(p => p.Value).ThenBy(p => p.Key).Select(p => p.Key).Concat(StandbyValidators).Take(validators_count)
        #        }

        raise NotImplementedError()

    def GetNextBlockHash(self, hash):
        if isinstance(hash, (UInt256, bytes)):
            header = self.GetHeader(hash)
        else:
            # unclear why this branch exists
            header = self.GetHeader(hash.ToBytes())

        if header:
            if header.Index + 1 >= len(self._header_index):
                return None
            return self._header_index[header.Index + 1]
        return None

    def GetScript(self, script_hash):
        return self.GetContract(script_hash)

    def GetSysFeeAmountByHeight(self, height):
        """
        Get the system fee for the specified block.

        Args:
            height (int): block height.

        Returns:
            int:
        """
        hash = self.GetBlockHash(height)
        return self.GetSysFeeAmount(hash)

    def OnPersistCompleted(self, block):
        self.PersistCompleted.on_change(block)
        msgrouter.on_block_persisted(block)

    @property
    def BlockCacheCount(self):
        return len(self._block_cache)

    def Pause(self):
        self._paused = True

    def Resume(self):
        self._paused = False

    async def Persist(self, block):

        self._persisting_block = block

        snapshot = self._db.createSnapshot()
        snapshot.PersistingBlock = block

        amount_sysfee = self.GetSysFeeAmount(block.PrevHash) + (block.TotalFees().value / Fixed8.D)
        amount_sysfee_bytes = struct.pack("<d", amount_sysfee)
        to_dispatch = []

        with self._db.getBatch() as wb:
            wb.put(DBPrefix.DATA_Block + block.Hash.ToBytes(), amount_sysfee_bytes + block.Trim())

            for tx_idx, tx in enumerate(block.Transactions):
                with self._db.getBatch() as tx_wb:
                    tx_wb.put(DBPrefix.DATA_Transaction + tx.Hash.ToBytes(), block.IndexBytes() + tx.ToArray())

                    # go through all outputs and add unspent coins to them

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
                                           Fixed8(0), tx.Precision, Fixed8(0),
                                           Fixed8(0), UInt160(data=bytearray(20)),
                                           tx.Owner, tx.Admin, tx.Admin,
                                           block.Index + 2 * 2000000, False)

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
                    elif tx.Type == TransactionType.StateTransaction:
                        # @TODO Implement persistence for State Descriptors
                        pass

                    elif tx.Type == TransactionType.PublishTransaction:
                        def create_contract_state():
                            return ContractState(tx.Code, tx.NeedStorage, tx.Name, tx.CodeVersion,
                                                 tx.Author, tx.Email, tx.Description)

                        snapshot.Contracts.GetOrAdd(tx.Code.ScriptHash().ToBytes(), create_contract_state)
                    elif tx.Type == TransactionType.InvocationTransaction:

                        engine = ApplicationEngine(TriggerType.Application, tx, snapshot.Clone(), tx.Gas)
                        engine.LoadScript(tx.Script)

                        try:
                            success = engine.Execute()
                            if success:
                                engine._Service.Commit()
                                engine._Service.ExecutionCompleted(engine, success)
                            else:
                                engine._Service.ExecutionCompleted(engine, False)

                        except Exception as e:
                            traceback.print_exc()

                        to_dispatch = to_dispatch + engine._Service.events_to_dispatch
                        await asyncio.sleep(0.001)

                    else:
                        if tx.Type != b'\x00' and tx.Type != b'\x80':
                            logger.info("TX Not Found %s " % tx.Type)

            snapshot.Commit()
            snapshot.Dispose()

            wb.put(DBPrefix.SYS_CurrentBlock, block.Hash.ToBytes() + block.IndexBytes())
            self._current_block_height = block.Index
            self._persisting_block = None

            self.TXProcessed += len(block.Transactions)

        for event in to_dispatch:
            events.emit(event.event_type, event)

    async def TryPersist(self, block) -> Tuple[bool, str]:
        distance = self._current_block_height - block.Index

        if distance >= 0:
            return False, "Block already exists"

        if distance < -1:
            return False, f"Trying to persist block {block.Index} but expecting next block to be {self._current_block_height + 1}"

        try:
            await self.Persist(block)
        except Exception as e:
            traceback.print_exc()
            return False, f"{e}"

        return True, ""

    def Dispose(self):
        self._db.closeDB()
        self._disposed = True

    @staticmethod
    def RegisterBlockchain(blockchain):
        """
        Register the default block chain instance.

        Args:
            blockchain: a blockchain instance. E.g. neo.Storage.Implementation.LevelDB.LevelDBImpl
        """
        if Blockchain._instance is None:
            Blockchain._instance = blockchain

    @staticmethod
    def DeregisterBlockchain():
        """
        Remove the default blockchain instance.
        """
        Blockchain.SECONDS_PER_BLOCK = 15
        Blockchain.DECREMENT_INTERVAL = 2000000
        Blockchain.GENERATION_AMOUNT = [8, 7, 6, 5, 4, 3, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        Blockchain._blockchain = None
        Blockchain._validators = []
        Blockchain._genesis_block = None
        Blockchain._instance = None
        Blockchain._blockrequests = set()
        Blockchain._paused = False
        Blockchain.BlockSearchTries = 0
        Blockchain.CACHELIM = 4000
        Blockchain.CMISSLIM = 5
        Blockchain.LOOPTIME = .1
        Blockchain.PersistCompleted = Events()
        Blockchain.Notify = Events()
        Blockchain._instance = None
