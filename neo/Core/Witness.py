# -*- coding:utf-8 -*-

from neo.IO.Mixins import SerializableMixin
import sys
import json
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

    def Serialize(self, writer):
        writer.WriteVarBytes(self.InvocationScript)
        writer.WriteVarBytes(self.VerificationScript)

    def ToJson(self):
        data = {
            'invocation': ':'.join(x.encode('hex') for x in self.InvocationScript),
            'verification': ':'.join(x.encode('hex') for x in self.VerificationScript)
        }

        return json.dumps(data)