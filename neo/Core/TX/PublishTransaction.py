import sys
import binascii
from logzero import logger

from neo.Core.TX.Transaction import Transaction, TransactionType
from neo.Core.FunctionCode import FunctionCode
from neo.Settings import settings
from neo.Fixed8 import Fixed8


class PublishTransaction(Transaction):

    Code = None
    NeedStorage = False
    Name = ''
    CodeVersion = ''
    Author = ''
    Email = ''
    Description = ''

    def __init__(self, *args, **kwargs):
        super(PublishTransaction, self).__init__(*args, **kwargs)
        self.Type = TransactionType.PublishTransaction

    def SystemFee(self):
        return Fixed8(int(settings.PUBLISH_TX_FEE))

    def DeserializeExclusiveData(self, reader):
        if self.Version > 1:
            logger.error("format exception...")

        self.Code = FunctionCode()
        self.Code.Deserialize(reader)

        if self.Version >= 1:
            self.NeedStorage = reader.ReadBool()
        else:
            self.NeedStorage = False

        self.Name = reader.ReadVarString()
        self.CodeVersion = reader.ReadVarString()
        self.Author = reader.ReadVarString()
        self.Email = reader.ReadVarString()
        self.Description = reader.ReadVarString()

    def SerializeExclusiveData(self, writer):

        self.Code.Serialize(writer)

        if self.Version >= 1:
            writer.WriteBool(self.NeedStorage)

        writer.WriteVarString(self.Name)
        writer.WriteVarString(self.CodeVersion)
        writer.WriteVarString(self.Author)
        writer.WriteVarString(self.Email)
        writer.WriteVarString(self.Description)

    def ToJson(self):
        jsn = super(PublishTransaction, self).ToJson()
        jsn['contract'] = {}
        jsn['contract']['code'] = self.Code.ToJson()
        jsn['contract']['needstorage'] = self.NeedStorage
        jsn['contract']['name'] = self.Name.decode('utf-8')
        jsn['contract']['version'] = self.CodeVersion.decode('utf-8')
        jsn['contract']['author'] = self.Author.decode('utf-8')
        jsn['contract']['email'] = self.Email.decode('utf-8')
        jsn['contract']['description'] = self.Description.decode('utf-8')
        return jsn
