# -*- coding:utf-8 -*-

from AntShares.Core.Block import Block
from AntShares.Core.AssetType import AssetType
from AntShares.Core.TX.RegisterTransaction import RegisterTransaction
from AntShares.Core.Witness import Witness
from AntShares.Core.Scripts.ScriptOp import *
from AntShares.Cryptography.ECCurve import *

from datetime import datetime
### not sure of the origin of these
Issuer = '030fe41d11cc34a667cf1322ddc26ea4a8acad3b8eefa6f6c3f49c7673e4b33e4b'
Admin = '9c17b4ee1441676e36d77a141dd77869d271381d'


class Blockchain(object):


    SECONDS_PER_BLOCK = 15

    DECREMENT_INTERVAL = 2000000

    GENERATION_AMOUNT = [ 8, 7, 6, 5, 4, 3, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 ]

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
        next_consensus = Blockchain.GetConsensusAddress(StandbyValidators)
        script = Witness( bytes(0), bytes(ScriptOp.PUSHT))

#        mt = Min

        return Block()


    @staticmethod
    def GetConsensusAddress(standby_validators):
        raise NotImplementedError()

    @staticmethod
    def Default():
        raise NotImplementedError()