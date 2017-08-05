

from neo.Core.TX.Transaction import Transaction,TransactionType
import sys
from neo.Core.FunctionCode import FunctionCode

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


    def DeserializeExclusiveData(self, reader):
        if self.Version > 1:
            print("format exception...")

        self.Code = FunctionCode()
        self.Code.Deserialize(reader)

        if self.Version >= 1:
            self.NeedStorage = reader.ReadBoolean()
        else:
            self.NeedStorage = False

        self.Name = reader.ReadVarString().decode('utf-8')
        self.CodeVersion = reader.ReadVarString().decode('utf-8')
        self.Author = reader.ReadVarString().decode('utf-8')
        self.Email = reader.ReadVarString().decode('utf-8')
        self.Description = reader.ReadVarString().decode('utf-8')

    def SerializeExclusiveData(self, writer):

        self.Code.Serialize(writer)

        if self.Version >=1:
            writer.WriteBoolean( self.NeedStorage)

        writer.WriteVarString(self.Name)

        writer.WriteVarString(self.CodeVersion)
        writer.WriteVarString(self.Author)
        writer.WriteVarString(self.Email)
        writer.WriteVarString(self.Description)



