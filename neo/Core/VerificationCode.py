from neo.SmartContract.ContractParameterType import ContractParameterType
from neo.Core.Cryptography.Crypto import Crypto
import binascii
from neo.logging import log_manager

logger = log_manager.getLogger()


class VerificationCode:
    @property
    def ScriptHash(self):

        if self._scriptHash is None:
            try:
                self._scriptHash = Crypto.ToScriptHash(self.Script)
            except binascii.Error:
                self._scriptHash = Crypto.ToScriptHash(self.Script, unhex=False)
            except Exception as e:
                logger.error("Could not create script hash: %s " % e)

        return self._scriptHash

    def __init__(self, script=None, param_list=None):
        self.Script = script
        self.ParameterList = param_list
        self.ReturnType = ContractParameterType.Boolean
        self._scriptHash = None
