
from neo.SmartContract.ContractParameterType import ContractParameterType
from neo.Cryptography.Crypto import Crypto


class VerificationCode():

    Script = None

    ParameterList = None

    ReturnType = ContractParameterType.Boolean

    _scriptHash = None

    @property
    def ScriptHash(self):

        if self._scriptHash is None:

            self._scriptHash = Crypto.ToScriptHash(self.Script)

        return self._scriptHash

    def __init__(self, script=None, param_list=None):
        self.Script = script
        self.ParameterList = param_list
