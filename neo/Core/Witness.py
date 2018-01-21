import sys
import json
import binascii

from logzero import logger

from neocore.IO.Mixins import SerializableMixin


class Witness(SerializableMixin):

    InvocationScript = None
    VerificationScript = None

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
        return sys.getsizeof(self.InvocationScript) + sys.getsizeof(self.VerificationScript)

    def Deserialize(self, reader):
        self.InvocationScript = reader.ReadVarBytes()
        self.VerificationScript = reader.ReadVarBytes()

    def Serialize(self, writer):
        #        logger.info("Serializing Witnes.....")
        #        logger.info("INVOCATION %s " % self.InvocationScript)
        writer.WriteVarBytes(self.InvocationScript)
#        logger.info("writer after invocation %s " % writer.stream.ToArray())
#        logger.info("Now wringi verificiation script %s " % self.VerificationScript)
        writer.WriteVarBytes(self.VerificationScript)
#        logger.info("Wrote verification script %s " % writer.stream.ToArray())

    def ToJson(self):
        #        logger.info("invocation %s " % self.InvocationScript)
        data = {
            'invocation': self.InvocationScript.hex(),
            'verification': self.VerificationScript.hex()
        }

        return data
