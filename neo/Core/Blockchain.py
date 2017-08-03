# -*- coding:utf-8 -*-

from neo.Core.Block import Block
from neo.Core.AssetType import AssetType
from neo.Core.TX.Transaction import *
from neo.Core.TX.RegisterTransaction import RegisterTransaction
from neo.Core.TX.MinerTransaction import MinerTransaction
from neo.Core.TX.IssueTransaction import IssueTransaction
from neo.Core.Witness import Witness
from neo.Core.Scripts.ScriptOp import *
from neo.Core.SpentCoin import SpentCoin
from neo.Core.Helper import Helper
from neo.Wallets.Contract import Contract
from neo import Settings
from neo.Cryptography.Crypto import *
from neo.Cryptography.Helper import *
from collections import Counter
from neo.Fixed8 import Fixed8
from datetime import datetime
from events import Events
from neo.Cryptography.ECCurve import ECDSA
import pytz


### not sure of the origin of these
Issuer = ECDSA.decode_secp256r1( '030fe41d11cc34a667cf1322ddc26ea4a8acad3b8eefa6f6c3f49c7673e4b33e4b').G
Admin = b'Abf2qMs1pzQb8kYk9RuxtUb9jtRKJVuBJt'

class Blockchain(object):


    SECONDS_PER_BLOCK = 15

    DECREMENT_INTERVAL = 2000000

    GENERATION_AMOUNT = [ 8, 7, 6, 5, 4, 3, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 ]

    __blockchain = None

    __validators = []

    __genesis_block=None

    __instance = None


    PersistCompleted = Events()

    @staticmethod
    def StandbyValidators():
        if len(Blockchain.__validators) < 1:
            vlist = Settings.STANDBY_VALIDATORS
            for pkey in Settings.STANDBY_VALIDATORS:
                Blockchain.__validators.append( ECDSA.decode_secp256r1(pkey).G)

        return Blockchain.__validators

    @staticmethod
    def SystemShare():
        amount =Fixed8.FromDecimal(  sum(Blockchain.GENERATION_AMOUNT) * Blockchain.DECREMENT_INTERVAL )
        owner = bytes(0)
        admin = Crypto.Hash160(ScriptOp.PUSHT)
        return RegisterTransaction([],[], AssetType.AntShare,
                                 "[{\"lang\":\"zh-CN\",\"name\":\"小蚁股\"},{\"lang\":\"en\",\"name\":\"AntShare\"}]",
                                 amount,0, owner, admin)

    @staticmethod
    def SystemCoin():
        amount =Fixed8.FromDecimal(  sum(Blockchain.GENERATION_AMOUNT) * Blockchain.DECREMENT_INTERVAL)

        owner = 0
        precision=8
        admin = Crypto.Hash160(ScriptOp.PUSHF)

        return RegisterTransaction([],[], AssetType.AntCoin,
                                         "[{\"lang\":\"zh-CN\",\"name\":\"小蚁币\"},{\"lang\":\"en\",\"name\":\"AntCoin\"}]",
                                         amount,precision,owner, admin)

    @staticmethod
    def GenesisBlock():


        prev_hash = bytearray(32)
        timestamp = int(datetime(2016, 7, 15, 15, 8, 21, tzinfo= pytz.utc ).timestamp())
        index = 0
        consensus_data = 2083236893 #向比特币致敬 ( Pay Tribute To Bitcoin )
        next_consensus = Blockchain.GetConsensusAddress(Blockchain.StandbyValidators())
        script = Witness( bytearray(0), bytearray(ScriptOp.PUSHT))

        mt = MinerTransaction()
        mt.Nonce = 2083236893

        output = TransactionOutput(
            Blockchain.SystemShare().HashToString(),
            Blockchain.SystemShare().Amount,
            Helper.RawBytesToScriptHash(Contract.CreateMultiSigRedeemScript(int(len(Blockchain.StandbyValidators()) / 2) + 1, Blockchain.StandbyValidators()))
        )

        it = IssueTransaction([],[output],[], [script])

        return Block(prev_hash,timestamp,index,consensus_data,
                     next_consensus,script,
                     [mt,Blockchain.SystemShare(),Blockchain.SystemCoin(),it],
                     True)


    @staticmethod
    def Default():
        if Blockchain.__instance is None:

            Blockchain.__instance = Blockchain()
            Blockchain.GenesisBlock().RebuildMerkleRoot()

        return Blockchain.__instance


    def CurrentBlockHash(self):
        # abstract
        pass

    def CurrentHeaderHash(self):
        # abstract
        pass

    def HeaderHeight(self):
        # abstract
        pass

    def Height(self):
        # abstract
        pass

    def AddBlock(self, block):
        # abstract
        pass

    def AddHeaders(self, headers):
        # abstract
        pass

    @staticmethod
    def CalculateBonusIgnoreClaimed(inputs, ignore_claimed=True):
        raise NotImplementedError()

    @staticmethod
    def CalculateBonus(inputs, height_end):
        unclaimed = []
        hashes = Counter([input.PrevHash for input in inputs]).items()
        for hash in hashes:
            height_start=0
            tx,height = Blockchain.Default().getTransaction(hash)
            height_start = height
            if tx is None: return False
            if height_start == height_end: continue

            to_be_checked = []
            [to_be_checked.append(input) for input in inputs if input.PrevHash == hash]

            for claim in to_be_checked:

                if claim.PrevIndex >= len(tx.Outputs) or tx.Outputs[claim.PrevIndex].AssetId == Blockchain.SystemShare().Hash():
                    raise Exception('Invalid claim')


                coin = SpentCoin(tx.Outputs[claim.PrevIndex], height_start, height_end)
                unclaimed.append(coin)

        return Blockchain.CalculateBonusInternal(unclaimed)


    @staticmethod
    def CalculateBonusInternal(unclaimed):
        amount_claimed = Fixed8(0)

        raise NotImplementedError()

    def ContainsBlock(self,hash):
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

    def GetAccountState(self, script_hash):
        # abstract
        pass

    def GetAssetState(self, assetId):
        # abstract
        pass

    def GetBlock(self, height):
        return self.GetBlockByHash(self.GetBlockHash(height))

    def GetBlockByHash(self, hash):
        # abstract
        pass

    def GetBlockHash(self, height):
        # abstract
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
        script = Contract.CreateMultiSigRedeemScript(vlen - int((vlen - 1)/3) , validators)
        return Helper.RawBytesToScriptHash(script)

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
        #abstract
        pass

    def GetScript(self, script_hash):
        return self.GetContract(script_hash)

    def GetStorageItem(self, key):
        #abstract
        pass

    def GetSysFeeAmount(self, hash):
        #abstract
        pass

    def GetTransaction(self, hash):
        # abstract
        # should return both transaction and height
        # return tx, height
        pass

    def GetUnClaimed(self, hash):
        #abstract
        pass

    def GetUnspent(self, hash, index):
        #abstract
        pass


    def GetVotes(self, transactions):
        # abstract
        pass

    def IsDoubleSpend(self, tx):
        # abstract
        pass

    def OnPersistCompleted(self, block):

        self.__validators = []

    @staticmethod
    def RegisterBlockchain(blockchain):
        Blockchain.__instance = blockchain
        print("registered blockchain, instance is: %s " % Blockchain.__instance)