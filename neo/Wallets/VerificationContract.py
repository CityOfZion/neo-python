from neo.SmartContract.Contract import Contract
from neo.Cryptography.Crypto import Crypto
from neo.SmartContract.ContractParameterType import ContractParameterType
from neo.VM.OpCode import CHECKSIG
from neo.IO.Helper import Helper as IOHelper


class VerificationContract(Contract):
    def __init__(self, redeem_script=None, param_list=None, pubkey_hash=None):
        super(VerificationContract, self).__init__(
            redeem_script=redeem_script,
            param_list=param_list,
            pubkey_hash=pubkey_hash
        )

    @property
    def IsStandard(self):
        """
        XXXUnknown.

        Returns:
             bool: True if standard, False otherwise.
        """
        scp = self.Script

        if len(scp) != 35:
            return False

        if scp[0] != 33 or scp[34] != int.from_bytes(CHECKSIG, 'little'):
            return False

        return True

    @property
    def ScriptHash(self):
        """
        Get the ScriptHash.

        Returns:
            UInt160: script hash
        """
        if self._scriptHash is None:
            self._scriptHash = Crypto.ToScriptHash(self.Script, unhex=False)
        return self._scriptHash

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        return self.PublicKeyHash.Size + IOHelper.GetVarSize(self.ParameterList) + IOHelper.GetVarSize(self.Script)

    @staticmethod
    def Create(redeemScript, parameterList, publicKeyHash):
        """
        Create a Verification contract.

        Args:
            redeemScript (bytes):
            parameterList (ContractParameterType):
            publicKeyHash (UInt160)

        Returns:
            VerificationContract:
        """
        return VerificationContract(redeemScript, parameterList, publicKeyHash)

    @staticmethod
    def CreateSignatureContract(publicKey):
        """
        Create a Signature type VerificationContract.

        Args:
            publicKey (edcsa.Curve.point): i.e. KeyPair.PublicKey.

        Returns:
            VerificationContract:
        """
        script = bytes.fromhex(
            Contract.CreateSignatureRedeemScript(publicKey).decode('utf8'))
        params = bytearray([ContractParameterType.Signature])
        encoded = publicKey.encode_point(True)
        pubkey_hash = Crypto.ToScriptHash(encoded, unhex=True)
        return VerificationContract(script, params, pubkey_hash)

    def Deserialize(self, reader):
        """
         Deserialize full object.

         Args:
             reader(neo.IO.BinaryReader):
        """
        self.PublicKeyHash = reader.ReadUInt160()
        self.ParameterList = [reader.ReadVarBytes()]
        self.Script = reader.ReadVarBytes()

    def Serialize(self, writer):
        """
         Serialize full object.

         Args:
             reader(neo.IO.BinaryReader):
        """
        writer.WriteUInt160(self.PublicKeyHash)

        bytes_list = b''
        for p in self.ParameterList:
            bytes_list += p

        # writer.WriteVarBytes(ParameterList.Cast<byte>().ToArray());
        writer.WriteVarBytes(bytes_list)
        writer.WriteVarBytes(self.Script)
