# -*- coding:utf-8 -*-

from AntShares.Core.Block import Block
from AntShares.Core.AssetType import AssetType
from AntShares.Core.TX.Transaction import *
from AntShares.Core.TX.RegisterTransaction import RegisterTransaction
from AntShares.Core.TX.MinerTransaction import MinerTransaction
from AntShares.Core.TX.IssueTransaction import IssueTransaction
from AntShares.Core.Witness import Witness
from AntShares.Core.Scripts.ScriptOp import *
from AntShares.Core.SpentCoin import SpentCoin
from AntShares.Wallets.Contract import Contract
from collections import Counter
from AntShares.Fixed8 import Fixed8
from datetime import datetime
from bitarray import bitarray
### not sure of the origin of these
Issuer = '030fe41d11cc34a667cf1322ddc26ea4a8acad3b8eefa6f6c3f49c7673e4b33e4b'
Admin = '9c17b4ee1441676e36d77a141dd77869d271381d'


class Blockchain(object):


    SECONDS_PER_BLOCK = 15

    DECREMENT_INTERVAL = 2000000

    GENERATION_AMOUNT = [ 8, 7, 6, 5, 4, 3, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 ]

    __blockchain = None

    __validators = []

    __genesis_block=None

    __instance = None


    @staticmethod
    def StandbyValidators():
        raise NotImplementedError()

    @staticmethod
    def SystemShare():
        amount =sum(Blockchain.GENERATION_AMOUNT) * Blockchain.DECREMENT_INTERVAL
        return RegisterTransaction([],[], AssetType.AntShare,
                                 "[{\"lang\":\"zh-CN\",\"name\":\"小蚁股\"},{\"lang\":\"en\",\"name\":\"AntShare\"}]",
                                 amount,Issuer,Admin)

    @staticmethod
    def SystemCoin():
        amount =sum(Blockchain.GENERATION_AMOUNT) * Blockchain.DECREMENT_INTERVAL
        return RegisterTransaction([],[], AssetType.AntCoin,
                                 "[{\"lang\":\"zh-CN\",\"name\":\"小蚁币\"},{\"lang\":\"en\",\"name\":\"AntCoin\"}]",
                                 amount,Issuer,Admin)

    @staticmethod
    def GenesisBlock():


        prev_hash = 0
        timestamp = datetime(2016, 7, 15, 15, 8, 21 ).time()
        index = 0
        consensus_data = 2083236893 #向比特币致敬
        next_consensus = Blockchain.GetConsensusAddress(Blockchain.StandbyValidators())
        script = Witness( bitarray(0), bitarray(ScriptOp.PUSHT))

        mt = MinerTransaction()
        mt.Nonce = 2083236893

        output = TransactionOutput(
            AssetType.AntShare,
            Blockchain.SystemShare().Amount,
            Contract.CreateMultiSigRedeemScript(len(Blockchain.StandbyValidators()) / 2, Blockchain.StandbyValidators()).ToScriptHash()
        )

        it = IssueTransaction([],[output],[], [script])

        return Block(prev_hash,timestamp,index,consensus_data,next_consensus,script,[mt,Blockchain.SystemShare(),Blockchain.SystemCoin(),it])


    @staticmethod
    def GetConsensusAddress(standby_validators):
        raise NotImplementedError()

    @staticmethod
    def Default():
        if Blockchain.__instance is None:

            Blockchain.__instance = Blockchain()
            Blockchain.GenesisBlock().RebuildMerkleRoot()


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

    def ContainsBlock(selfhash):
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

    def GetHeader(self, height):
        # abstract
        pass



    @staticmethod
    def GetConsensusAddress(validators):
        vlen = len(validators)
        return Contract.CreateMultiSigRedeemScript(vlen - ((vlen-1)/3), validators).ToScriptHash()

    def GetValidators(self):

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