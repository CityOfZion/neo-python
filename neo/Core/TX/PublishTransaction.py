from neo.Core.TX.Transaction import Transaction, TransactionType
from neo.Core.FunctionCode import FunctionCode
from neo.Core.Size import GetVarSize
from neo.Core.Size import Size as s
from neo.logging import log_manager

logger = log_manager.getLogger()


class PublishTransaction(Transaction):
    def __init__(self, *args, **kwargs):
        """
        Create instance.

        Args:
            *args:
            **kwargs:
        """
        super(PublishTransaction, self).__init__(*args, **kwargs)
        self.Type = TransactionType.PublishTransaction
        self.Code = None
        self.NeedStorage = False
        self.Name = ''
        self.CodeVersion = ''
        self.Author = ''
        self.Email = ''
        self.Description = ''

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        return super(PublishTransaction, self).Size() + GetVarSize(self.Code.Script) + GetVarSize(self.Code.ParameterList) + s.uint8 + GetVarSize(
            self.Name) + GetVarSize(self.CodeVersion) + GetVarSize(self.Author) + GetVarSize(self.Email) + GetVarSize(self.Description)

    def DeserializeExclusiveData(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neo.IO.BinaryReader):
        """
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
        """
        Serialize object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        self.Code.Serialize(writer)

        if self.Version >= 1:
            writer.WriteBool(self.NeedStorage)

        writer.WriteVarString(self.Name)
        writer.WriteVarString(self.CodeVersion)
        writer.WriteVarString(self.Author)
        writer.WriteVarString(self.Email)
        writer.WriteVarString(self.Description)

    def ToJson(self):
        """
        Convert object members to a dictionary that can be parsed as JSON.

        Returns:
             dict:
        """
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
