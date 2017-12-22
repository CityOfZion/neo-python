import binascii
from neo.IO.Mixins import SerializableMixin

class Witness(SerializableMixin):

    InvocationScript = None
    VerificationScript = None

    def __init__(self, invocation_script=bytearray(), verification_script=bytearray()):
        """
        Create an instance.

        Args:
            invocation_script (bytearray): the invocation script.
            verification_script (bytearray): the verification script.

        Throws:
            ValueError: if parameter types are incorrect.
            Exception: if verification_script is a string.
        """

        # def __init__(self, invocation_script=bytearray(), verification_script=bytearray()):
        if not isinstance(invocation_script, (bytearray, bytes)):
            raise ValueError(
                'Invalid invocation_script parameter type: {} is not of type bytearray or bytes'.format(
                    type(invocation_script)))

        if not isinstance(verification_script, (bytearray, bytes)):
            raise ValueError(
                'Invalid verification_script parameter type: {} is not of type bytearray or bytes '.format(
                    type(verification_script)))

        try:
            self.InvocationScript = binascii.unhexlify(invocation_script)
        except binascii.Error:
            self.InvocationScript = invocation_script

        try:
            self.VerificationScript= binascii.unhexlify(verification_script)
        except binascii.Error:
            self.VerificationScript = verification_script


        # if not isinstance(invocation_script, (bytearray, bytes)):
        #     raise ValueError('Invalid invocation_script parameter type: {} is not of type bytearray, bytes or str'.format(type(invocation_script)))
        #
        # try:
        #     self.InvocationScript = binascii.unhexlify(invocation_script)
        # except Exception as e:
        #     self.InvocationScript = invocation_script
        #
        # if type(verification_script) is str:
        #     raise Exception("Cannot be string")
        #
        # try:
        #     self.VerificationScript = binascii.unhexlify(verification_script)
        # except Exception as e:
        #     self.VerificationScript = verification_script

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        from neo.IO.Helper import Helper as IOHelper
        return IOHelper.GetVarSize(self.InvocationScript) + IOHelper.GetVarSize(self.VerificationScript)

    def Deserialize(self, reader):
        """
        Deserialize full object.

        Args:
            reader(neo.IO.BinaryReader):
        """
        self.InvocationScript = reader.ReadVarBytes()
        self.VerificationScript = reader.ReadVarBytes()

    def Serialize(self, writer):
        """
        Serialize full object.

        Args:
            reader(neo.IO.BinaryReader):
        """
        writer.WriteVarBytes(self.InvocationScript)
        writer.WriteVarBytes(self.VerificationScript)

    def ToJson(self):
        """
        Convert object members to dictionary that can be parsed as JSON.

        Returns:
             dict:
        """
        #        logger.info("invocation %s " % self.InvocationScript)
        data = {
            'invocation': self.InvocationScript.hex(),
            'verification': self.VerificationScript.hex()
        }

        return data
