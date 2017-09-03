# -*- coding:utf-8 -*-

from neo.IO.Mixins import SerializableMixin
import sys
import json
import binascii
class Witness(SerializableMixin):

    InvocationScript=None
    VerificationScript=None

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
#        print("Serializing Witnes.....")
#        print("INVOCATION %s " % self.InvocationScript)
        writer.WriteVarBytes(self.InvocationScript)
#        print("writer after invocation %s " % writer.stream.ToArray())
#        print("Now wringi verificiation script %s " % self.VerificationScript)
        writer.WriteVarBytes(self.VerificationScript)
#        print("Wrote verification script %s " % writer.stream.ToArray())

    def ToJson(self):
#        print("invocation %s " % self.InvocationScript)
        data = {
            'invocation': self.InvocationScript.hex(),
            'verification': self.VerificationScript.hex()
        }

        return data