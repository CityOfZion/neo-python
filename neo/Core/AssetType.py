# -*- coding:utf-8 -*-
"""
Description:
    Asset Type in neo
Usage:
    from neo.Core.AssetType import AssetType
"""


class AssetType(object):
    CreditFlag = 0x40
    DutyFlag = 0x80

    GoverningToken = 0x00
    UtilityToken = 0x01
    Currency = 0x08

    Share = DutyFlag | 0x10
    Invoice = DutyFlag | 0x18
    Token = CreditFlag | 0x20

    @staticmethod
    def AllTypes():
        """
        Get a list of all available asset types.

        Returns:
            list: of AssetType items.
        """
        return [AssetType.CreditFlag, AssetType.DutyFlag, AssetType.GoverningToken,
                AssetType.UtilityToken, AssetType.Currency, AssetType.Share,
                AssetType.Invoice, AssetType.Token]
