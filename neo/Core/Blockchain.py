# -*- coding:utf-8 -*-

from neo.Core.Block import Block
from neo.Core.TX.Transaction import *
from neo.Core.TX.RegisterTransaction import RegisterTransaction
from neo.Core.TX.MinerTransaction import MinerTransaction
from neo.Core.TX.IssueTransaction import IssueTransaction
from neo.Core.Witness import Witness
from neo.VM.OpCode import *
from neo.Core.State.SpentCoinState import SpentCoin
from neo.SmartContract.Contract import Contract
from neo.Settings import settings
from neo.Cryptography.Crypto import *
from neo.Cryptography.Helper import *
from collections import Counter
from neo.Fixed8 import Fixed8
from datetime import datetime
from events import Events
from neo.Cryptography.ECCurve import ECDSA
import pytz
from neo.UInt256 import UInt256
from itertools import groupby


class Blockchain(object):

    SECONDS_PER_BLOCK = 15

    DECREMENT_INTERVAL = 2000000

    GENERATION_AMOUNT = [8, 7, 6, 5, 4, 3, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

    __blockchain = None

    __validators = []

    __genesis_block = None

    __instance = None

    __blockrequests = set()

    BlockSearchTries = 0

    CACHELIM = 4000
    CMISSLIM = 5
    LOOPTIME = .1

    PersistCompleted = Events()

    Notify = Events()

    @staticmethod
    def StandbyValidators():
        if len(Blockchain.__validators) < 1:
            vlist = settings.STANDBY_VALIDATORS
            for pkey in settings.STANDBY_VALIDATORS:
                Blockchain.__validators.append(ECDSA.decode_secp256r1(pkey).G)

        return Blockchain.__validators

    @staticmethod
    def SystemShare():
        amount = Fixed8.FromDecimal(sum(Blockchain.GENERATION_AMOUNT) * Blockchain.DECREMENT_INTERVAL)
        owner = ECDSA.secp256r1().Curve.Infinity
        admin = Crypto.ToScriptHash(PUSHT)
        return RegisterTransaction([], [], AssetType.GoverningToken,
                                   "[{\"lang\":\"zh-CN\",\"name\":\"小蚁股\"},{\"lang\":\"en\",\"name\":\"AntShare\"}]",
                                   amount, 0, owner, admin)

    @staticmethod
    def SystemCoin():
        amount = Fixed8.FromDecimal(sum(Blockchain.GENERATION_AMOUNT) * Blockchain.DECREMENT_INTERVAL)

        owner = ECDSA.secp256r1().Curve.Infinity

        precision = 8
        admin = Crypto.ToScriptHash(PUSHF)

        return RegisterTransaction([], [], AssetType.UtilityToken,
                                   "[{\"lang\":\"zh-CN\",\"name\":\"小蚁币\"},{\"lang\":\"en\",\"name\":\"AntCoin\"}]",
                                   amount, precision, owner, admin)

    @staticmethod
    def GenesisBlock():

        prev_hash = UInt256(data=bytearray(32))
        timestamp = int(datetime(2016, 7, 15, 15, 8, 21, tzinfo=pytz.utc).timestamp())
        index = 0
        consensus_data = 2083236893  # 向比特币致敬 ( Pay Tribute To Bitcoin )
        next_consensus = Blockchain.GetConsensusAddress(Blockchain.StandbyValidators())
        script = Witness(bytearray(0), bytearray(PUSHT))

        mt = MinerTransaction()
        mt.Nonce = 2083236893

        output = TransactionOutput(
            Blockchain.SystemShare().Hash,
            Blockchain.SystemShare().Amount,
            Crypto.ToScriptHash(Contract.CreateMultiSigRedeemScript(int(len(Blockchain.StandbyValidators()) / 2) + 1, Blockchain.StandbyValidators()))
        )

        it = IssueTransaction([], [output], [], [script])

        return Block(prev_hash, timestamp, index, consensus_data,
                     next_consensus, script,
                     [mt, Blockchain.SystemShare(), Blockchain.SystemCoin(), it],
                     True)

    @staticmethod
    def Default():
        if Blockchain.__instance is None:

            Blockchain.__instance = Blockchain()
            Blockchain.GenesisBlock().RebuildMerkleRoot()

        return Blockchain.__instance

    @property
    def CurrentBlockHash(self):
        # abstract
        pass

    @property
    def CurrentHeaderHash(self):
        # abstract
        pass

    @property
    def HeaderHeight(self):
        # abstract
        pass

    @property
    def Height(self):
        # abstract
        pass

    def AddBlock(self, block):
        # abstract
        pass

    def AddHeaders(self, headers):
        # abstract
        pass

    @property
    def BlockRequests(self):
        return self.__blockrequests

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
                spent_coin = SpentCoin(output=tx.outputs[coinref.PrevIndex], start_height=height_start, end_height=height_end)
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
            startamount = 0 if coinheight.start == 0 else Blockchain.Default().GetSysFeeAmountByHeight(coinheight.start - 1)
            amount += endamount - startamount

            outputSum = 0

            for spentcoin in group:
                outputSum += spentcoin.Value.value

            outputSum = outputSum / 100000000
            outputSumFixed8 = Fixed8(int(outputSum * amount))
            amount_claimed += outputSumFixed8

        return amount_claimed

    def OnNotify(self, notification):
        #        print("on notifiy %s " % notification)
        self.Notify.on_change(notification)

    def ContainsBlock(self, hash):
        # abstract
        pass

    def ContainsTransaction(self, hash):
        # abstract
        pass

    def ContainsUnspent(self, hash, index):
        # abstract
        pass

    def Dispose(self):
        # abstract
        pass

    def GetAccountStateByIndex(self, index):
        pass

    def GetAccountState(self, script_hash):
        # abstract
        pass

    def GetAssetState(self, assetId):
        # abstract
        pass

    def SearchAssetState(self, query):
        pass

    def GetHeaderHash(self, height):
        pass

    def GetBlockByHeight(self, height):
        pass

    def GetBlock(self, height_or_hash):
        pass

    def GetBlockByHash(self, hash):
        # abstract
        pass

    def GetBlockHash(self, height):
        # abstract
        pass

    def GetSpentCoins(self, tx_hash):
        pass

    def GetAllSpentCoins(self):
        pass

    def SearchContracts(self, query):
        pass

    def ShowAllContracts(self):
        pass

    def GetContract(self, hash):
        # abstract
        pass

    def GetEnrollments(self):
        # abstract
        pass

    def GetHeader(self, hash):
        # abstract
        pass

    def GetHeaderByHeight(self, height):
        pass

    @staticmethod
    def GetConsensusAddress(validators):
        vlen = len(validators)
        script = Contract.CreateMultiSigRedeemScript(vlen - int((vlen - 1) / 3), validators)
        return Crypto.ToScriptHash(script)

    def GetValidators(self, others):

        votes = Counter([len(vs.PublicKeys) for vs in self.GetVotes(others)]).items()

# TODO: 此处排序可能将耗费大量内存，考虑是否采用其它机制
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
        # abstract
        pass

    def GetScript(self, script_hash):
        return self.GetContract(script_hash)

    def GetStorageItem(self, storage_key):
        # abstract
        pass

    def GetSysFeeAmount(self, hash):
        # abstract
        pass

    def GetSysFeeAmountByHeight(self, height):
        hash = self.GetBlockHash(height)
        return self.GetSysFeeAmount(hash)

    def GetTransaction(self, hash):
        return None, 0

    def GetUnclaimed(self, hash):
        # abstract
        pass

    def GetUnspent(self, hash, index):
        # abstract
        pass

    def GetVotes(self, transactions):
        # abstract
        pass

    def IsDoubleSpend(self, tx):
        # abstract
        pass

    def OnPersistCompleted(self, block):
        pass

    def BlockCacheCount(self):
        pass

    @staticmethod
    def RegisterBlockchain(blockchain):
        if Blockchain.__instance is None:
            Blockchain.__instance = blockchain

    @staticmethod
    def DeregisterBlockchain():
        Blockchain.__instance = None
