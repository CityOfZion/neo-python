# -*- coding:utf-8 -*-
"""
Description:
    Transaction Type in AntShares
Usage:
    from AntShares.Core.TransactionType import TransactionType
"""

class TransactionType(object):
    MinerTransaction = 0x00
    IssueTransaction = 0x01
    ClaimTransaction = 0x02
    EnrollmentTransaction = 0x20
    VotingTransaction = 0x24
    RegisterTransaction = 0x40
    ContractTransaction = 0x80
    AgencyTransaction = 0xb0
