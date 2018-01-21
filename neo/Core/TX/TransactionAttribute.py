# -*- coding:utf-8 -*-
"""
Description:
    Transaction Attribute
Usage:
    from neo.Core.TX.TransactionAttribute import TransactionAttribute
"""
from logzero import logger
from neo.Network.Inventory import Inventory
from neocore.IO.Mixins import SerializableMixin


class TransactionAttributeUsage(object):
    ContractHash = int.from_bytes(b'\x00', 'little')

    ECDH02 = int.from_bytes(b'\x02', 'little')
    ECDH03 = int.from_bytes(b'\x03', 'little')

    Script = int.from_bytes(b'\x20', 'little')

    Vote = int.from_bytes(b'\x30', 'little')

    CertUrl = int.from_bytes(b'\x80', 'little')
    DescriptionUrl = int.from_bytes(b'\x81', 'little')
    Description = int.from_bytes(b'\x90', 'little')

    Hash1 = int.from_bytes(b'\xa1', 'little')
    Hash2 = int.from_bytes(b'\xa2', 'little')
    Hash3 = int.from_bytes(b'\xa3', 'little')
    Hash4 = int.from_bytes(b'\xa4', 'little')
    Hash5 = int.from_bytes(b'\xa5', 'little')
    Hash6 = int.from_bytes(b'\xa6', 'little')
    Hash7 = int.from_bytes(b'\xa7', 'little')
    Hash8 = int.from_bytes(b'\xa8', 'little')
    Hash9 = int.from_bytes(b'\xa9', 'little')
    Hash10 = int.from_bytes(b'\xaa', 'little')
    Hash11 = int.from_bytes(b'\xab', 'little')
    Hash12 = int.from_bytes(b'\xac', 'little')
    Hash13 = int.from_bytes(b'\xad', 'little')
    Hash14 = int.from_bytes(b'\xae', 'little')
    Hash15 = int.from_bytes(b'\xaf', 'little')

    Remark = int.from_bytes(b'\xf0', 'little')
    Remark1 = int.from_bytes(b'\xf1', 'little')
    Remark2 = int.from_bytes(b'\xf2', 'little')
    Remark3 = int.from_bytes(b'\xf3', 'little')
    Remark4 = int.from_bytes(b'\xf4', 'little')
    Remark5 = int.from_bytes(b'\xf5', 'little')
    Remark6 = int.from_bytes(b'\xf6', 'little')
    Remark7 = int.from_bytes(b'\xf7', 'little')
    Remark8 = int.from_bytes(b'\xf8', 'little')
    Remark9 = int.from_bytes(b'\xf9', 'little')
    Remark10 = int.from_bytes(b'\xfa', 'little')
    Remark11 = int.from_bytes(b'\xfb', 'little')
    Remark12 = int.from_bytes(b'\xfc', 'little')
    Remark13 = int.from_bytes(b'\xfd', 'little')
    Remark14 = int.from_bytes(b'\xfe', 'little')
    Remark15 = int.from_bytes(b'\xff', 'little')


class TransactionAttribute(Inventory, SerializableMixin):
    MAX_ATTR_DATA_SIZE = 65535

    """docstring for TransactionAttribute"""

    def __init__(self, usage=None, data=None):
        """
        Create an instance.

        Args:
            usage (neo.Core.TX.TransactionAttribute.TransactionAttributeUsage):
            data (bytes):
        """
        super(TransactionAttribute, self).__init__()
        self.Usage = usage
        self.Data = data

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neo.IO.BinaryReader):
        """
        usage = reader.ReadByte()
        self.Usage = usage

        if usage == TransactionAttributeUsage.ContractHash or usage == TransactionAttributeUsage.Vote or \
                (usage >= TransactionAttributeUsage.Hash1 and usage <= TransactionAttributeUsage.Hash15):
            self.Data = reader.ReadBytes(32)

        elif usage == TransactionAttributeUsage.ECDH02 or usage == TransactionAttributeUsage.ECDH03:
            self.Data = bytearray(usage) + bytearray(reader.ReadBytes(32))

        elif usage == TransactionAttributeUsage.Script:
            self.Data = reader.ReadBytes(20)

        elif usage == TransactionAttributeUsage.DescriptionUrl:

            self.Data = reader.ReadBytes(reader.ReadByte())

        elif usage == TransactionAttributeUsage.Description or usage >= TransactionAttributeUsage.Remark:
            self.Data = reader.ReadVarBytes(max=self.MAX_ATTR_DATA_SIZE)
        else:
            logger.error("format error!!!")

    def Serialize(self, writer):
        """
        Serialize object.

        Args:
            writer (neo.IO.BinaryWriter):

        Raises:
            Exception: if the length exceeds the maximum allowed number of attributes in a transaction.
        """
        writer.WriteByte(self.Usage)

        length = len(self.Data)

        if length > self.MAX_ATTR_DATA_SIZE:
            raise Exception("Invalid transaction attribute")

        if self.Usage == TransactionAttributeUsage.ContractHash or self.Usage == TransactionAttributeUsage.Vote or \
                (self.Usage >= TransactionAttributeUsage.Hash1 and self.Usage <= TransactionAttributeUsage.Hash15):
            writer.WriteBytes(self.Data)

        elif self.Usage == TransactionAttributeUsage.ECDH02 or self.Usage == TransactionAttributeUsage.ECDH03:
            writer.WriteBytes(self.Data[1:33])

        elif self.Usage == TransactionAttributeUsage.Script:
            writer.WriteBytes(self.Data)

        elif self.Usage == TransactionAttributeUsage.DescriptionUrl:
            writer.WriteVarString(self.Data)

        elif self.Usage == TransactionAttributeUsage.Description or self.Usage >= TransactionAttributeUsage.Remark:
            writer.WriteVarString(self.Data)
        else:
            logger.error("format error!!!")

    def ToJson(self):
        """
        Convert object members to a dictionary that can be parsed as JSON.

        Returns:
             dict:
        """
        obj = {
            'usage': self.Usage,
            'data': '' if not self.Data else self.Data.hex()
        }
        return obj
