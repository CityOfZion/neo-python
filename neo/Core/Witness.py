import binascii
from neo.Core.IO.Mixins import SerializableMixin
from neo.Core.Size import GetVarSize


class Witness(SerializableMixin):

    def __init__(self, invocation_script=None, verification_script=None):
        try:
            self.InvocationScript = binascii.unhexlify(invocation_script)
        except Exception as e:
            self.InvocationScript = invocation_script

        if type(verification_script) is str:
            raise Exception("CAnnot be string")

        try:
            self.VerificationScript = binascii.unhexlify(verification_script)
        except Exception as e:
            self.VerificationScript = verification_script

    def Size(self):
        """
        Get the amount of bytes the serializable data of self consists off

        Returns:
            int:
        """
        return GetVarSize(self.InvocationScript) + GetVarSize(self.VerificationScript)

    def Deserialize(self, reader):
        self.InvocationScript = reader.ReadVarBytes()
        self.VerificationScript = reader.ReadVarBytes()

    def Serialize(self, writer):
        writer.WriteVarBytes(self.InvocationScript)
        writer.WriteVarBytes(self.VerificationScript)

    def ToJson(self):
        data = {
            'invocation': self.InvocationScript.hex(),
            'verification': self.VerificationScript.hex()
        }

        return data
