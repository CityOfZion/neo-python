"""
Description:
    Contract class in neo.Wallets
    Base class of all contracts
Usage:
    from neo.SmartContract.Contract import Contract
"""
import binascii
from neo.VM.OpCode import CHECKMULTISIG, CHECKSIG
from neo.VM.ScriptBuilder import ScriptBuilder
from neo.Core.Cryptography.Crypto import bin_hash160, Crypto
from neo.Core.IO.Mixins import SerializableMixin
from neo.Core.VerificationCode import VerificationCode
import neo.Core.Helper
from neo.Core.Cryptography.ECCurve import ECDSA


class ContractType:
    SignatureContract = 0
    MultiSigContract = 1
    CustomContract = 2


class Contract(SerializableMixin, VerificationCode):
    """docstring for Contract"""

    @property
    def Address(self):
        if self._address is None:
            self._address = Crypto.ToAddress(self.ScriptHash)
        return self._address

    @property
    def IsStandard(self):
        if len(self.Script) == 70:
            self.Script = binascii.unhexlify(self.Script)

        if len(self.Script) != 35:
            return False

        if self.Script[0] != 33 or self.Script[34] != int.from_bytes(CHECKSIG, 'little'):
            return False

        return True

    @property
    def IsMultiSigContract(self):
        scp = self.Script

        try:
            scp = binascii.unhexlify(self.Script)
        except binascii.Error:
            pass

        if len(scp) < 37:
            return False

        if scp[len(scp) - 1] != int.from_bytes(CHECKMULTISIG, 'little'):
            return False

        return True

    @property
    def Type(self):
        if self.IsStandard:
            return ContractType.SignatureContract
        elif self.IsMultiSigContract:
            return ContractType.MultiSigContract
        return ContractType.CustomContract

    def __init__(self, redeem_script=None, param_list=None, pubkey_hash=None):
        super(Contract, self).__init__()

        self.Script = redeem_script
        self.ParameterList = param_list
        self.PublicKeyHash = pubkey_hash
        self._address = None

    @staticmethod
    def Create(redeemScript, parameterList, publicKeyHash):

        return Contract(redeemScript, parameterList, publicKeyHash)

    @staticmethod
    def CreateMultiSigRedeemScript(m, publicKeys):

        if m < 1:
            raise Exception("Minimum required signature count is 1, specified {}.".format(m))

        if m > len(publicKeys):
            raise Exception("Invalid public key count. Minimum required signatures is bigger than supplied public keys count.")

        if len(publicKeys) > 1024:
            raise Exception("Supplied public key count ({}) exceeds maximum of 1024.".format(len(publicKeys)))

        sb = ScriptBuilder()
        sb.push(m)

        pkeys = [point for point in publicKeys]
        pkeys.sort()
        keys = [p.encode_point().decode() for p in pkeys]

        for key in keys:
            sb.push(key)

        sb.push(len(publicKeys))
        sb.add(CHECKMULTISIG)

        return sb.ToArray()

    @staticmethod
    def CreateMultiSigContract(publicKeyHash, m, publicKeys):

        pk = [ECDSA.decode_secp256r1(p).G for p in publicKeys]
        return Contract(Contract.CreateMultiSigRedeemScript(m, pk),
                        bytearray(m),
                        publicKeyHash)

    @staticmethod
    def CreateSignatureContract(publicKey):
        """
        Create a signature contract.

        Args:
            publicKey (edcsa.Curve.point): e.g. KeyPair.PublicKey.

        Returns:
            neo.SmartContract.Contract: a Contract instance.
        """
        script = Contract.CreateSignatureRedeemScript(publicKey)
        params = b'\x00'
        encoded = publicKey.encode_point(True)
        pubkey_hash = Crypto.ToScriptHash(encoded, unhex=True)

        return Contract(script, params, pubkey_hash)

    @staticmethod
    def CreateSignatureRedeemScript(publicKey):
        sb = ScriptBuilder()
        sb.push(publicKey.encode_point(compressed=True))
        sb.add(CHECKSIG)
        return sb.ToArray()

    def Equals(self, other):
        if id(self) == id(other):
            return True
        if not isinstance(other, Contract):
            return False
        return self.ScriptHash == other.ScriptHash

    def __eq__(self, other):
        return self.Equals(other)

    def ToScriptHash(self):
        return Crypto.Hash160(self.ScriptHash)

    def Deserialize(self, reader):
        self.PublicKeyHash = reader.ReadUInt160()
        self.ParameterList = reader.ReadVarBytes()
        # TODO: fix this. This is supposed to be `reader.ReadVarBytes`,
        #  however that no longer works after the internal implementation changed to verify the length of data to read.
        #  There has always been a bug that went unnoticed because previously we'd ask e.g. 70 bytes and it could return 35 without problems.
        #  Now that will fail. The test `neo.Wallets.test_wallet.test_privnet_wallet` thinks it should read 70 bytes because it expects b'AABB' data
        #  while in reality it gets b'\xAA\xBB` data and is thus only half the size. It's spread in so many places that I don't want to fix it in this already
        #  huge VM update PR. We work around it by manually reconstructing the old `ReadVarBytes``
        length = reader.ReadVarInt()
        script = bytearray(reader.ReadBytes(length))
        self.Script = script

    def Serialize(self, writer):
        writer.WriteUInt160(self.PublicKeyHash)
        writer.WriteVarBytes(self.ParameterList)
        if isinstance(self.Script, str):
            self.Script = self.Script.encode('utf-8')
        writer.WriteVarBytes(self.Script)

    @staticmethod
    def PubkeyToRedeem(pubkey):
        return binascii.unhexlify('21' + pubkey + 'ac')

    @staticmethod
    def RedeemToScripthash(redeem):
        return binascii.hexlify(bin_hash160(redeem))

    def ToArray(self):
        return neo.Core.Helper.Helper.ToArray(self)

    def ToJson(self):
        jsn = {}
        jsn['PublicKeyHash'] = self.PublicKeyHash.ToString()
        jsn['Parameters'] = bytes(self.ParameterList).decode('utf-8')
        jsn['Script'] = self.Script.decode('utf-8')
        return jsn
