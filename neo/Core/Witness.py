# -*- coding:utf-8 -*-

from neo.IO.Mixins import SerializableMixin
import sys
import json
import binascii
class Witness(SerializableMixin):

    InvocationScript=None
    VerificationScript=None

    def __init__(self, invocation_script=None, verification_script=None):
        self.InvocationScript = invocation_script
        self.VerificationScript = verification_script

    def Size(self):
        return sys.getsizeof(self.InvocationScript) + sys.getsizeof(self.VerificationScript)

    def Deserialize(self, reader):
        self.InvocationScript = reader.ReadVarBytes()
        self.VerificationScript = reader.ReadVarBytes()

        print("deserialized %s " % self.ToJson())


    def Serialize(self, writer):
        print("serializing witness!! %s " % self)
        writer.WriteVarBytes(self.InvocationScript)
        writer.WriteVarBytes(self.VerificationScript)

    def ToJson(self):
        data = {
            'invocation': binascii.hexlify( self.InvocationScript).decode('utf-8'),
            'verification': binascii.hexlify( self.VerificationScript).decode('utf-8')
        }

        return data