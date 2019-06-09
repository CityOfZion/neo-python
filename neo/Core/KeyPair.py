import hashlib
import unicodedata
import base58
import scrypt
import bitcoin
from Crypto.Cipher import AES
from neo.Core.Cryptography.ECCurve import ECDSA
from neo.Core.Cryptography.Crypto import Crypto
from neo.Core.Cryptography.Helper import xor_bytes

# NEP-2 constants
# https://github.com/neo-project/proposals/blob/master/nep-2.mediawiki
SCRYPT_ITERATIONS = 16384
SCRYPT_BLOCKSIZE = 8
SCRYPT_PARALLEL_FACTOR = 8
SCRYPT_KEY_LEN_BYTES = 64

NEP_HEADER = bytearray([0x01, 0x42])
NEP_FLAG = bytearray([0xe0])


class KeyPair(object):
    def setup_curve(self):
        """
        Setup the Elliptic curve parameters.
        """
        bitcoin.change_curve(
            115792089210356248762697446949407573530086143415290314195533631308867097853951,
            115792089210356248762697446949407573529996955224135760342422259061068512044369,
            115792089210356248762697446949407573530086143415290314195533631308867097853948,
            41058363725152142129326129780047268409114441015993725554835256314039467401291,
            48439561293906451759052585252797914202762949526041747995844080717082404635286,
            36134250956749795798585127919587881956611106672985015071877198253568414405109
        )

    def __init__(self, priv_key):
        """
        Create an instance.

        Args:
            priv_key (bytes): a private key.

        Raises:
            ValueError:
                if the input `priv_key` length is not 32, 96, or 104
                if the input `priv_key` length is 32 but the public key still could not be determined
        """
        self.setup_curve()
        self.PublicKeyHash = None
        self.PublicKey = None
        self.PrivateKey = None

        length = len(priv_key)

        if length != 32 and length != 96 and length != 104:
            raise ValueError("Invalid private key")

        self.PrivateKey = bytearray(priv_key[-32:])

        pubkey_encoded_not_compressed = None

        if length == 32:
            try:
                pubkey_encoded_not_compressed = bitcoin.privkey_to_pubkey(priv_key)
            except Exception:
                raise ValueError("Could not determine public key")

        elif length == 96 or length == 104:
            skip = length - 96
            pubkey_encoded_not_compressed = bytearray(b'\x04') + bytearray(priv_key[skip:skip + 64])

        if pubkey_encoded_not_compressed:
            pubkey_points = bitcoin.decode_pubkey(pubkey_encoded_not_compressed, 'bin')

            pubx = pubkey_points[0]
            puby = pubkey_points[1]
            edcsa = ECDSA.secp256r1()
            self.PublicKey = edcsa.Curve.point(pubx, puby)

        self.PublicKeyHash = Crypto.ToScriptHash(self.PublicKey.encode_point(True), unhex=True)

    @staticmethod
    def PrivateKeyFromWIF(wif):
        """
        Get the private key from a WIF key

        Args:
            wif (str): The wif key

        Returns:
            bytes: The private key

        Raises:
            ValueError:
                if the input `wif` length != 52
                if the input `wif` has an invalid format
                if the input `wif` has an invalid checksum
        """
        if wif is None or len(wif) is not 52:
            raise ValueError('Please provide a wif with a length of 52 bytes (LEN: {0:d})'.format(len(wif)))

        data = base58.b58decode(wif)

        length = len(data)

        if length is not 38 or data[0] is not 0x80 or data[33] is not 0x01:
            raise ValueError("Invalid format!")

        checksum = Crypto.Hash256(data[0:34])[0:4]

        if checksum != data[34:]:
            raise ValueError("Invalid WIF Checksum!")

        return data[1:33]

    @staticmethod
    def PrivateKeyFromNEP2(nep2_key, passphrase):
        """
        Gets the private key from a NEP-2 encrypted private key

        Args:
            nep2_key (str): The nep-2 encrypted private key
            passphrase (str): The password to encrypt the private key with, as unicode string

        Returns:
            bytes: The private key

        Raises:
            ValueError:
                if the input `nep2_key` length != 58
                if the input `nep2_key` is invalid
                if the input `passphrase` is wrong
        """
        if not nep2_key or len(nep2_key) != 58:
            raise ValueError('Please provide a nep2_key with a length of 58 bytes (LEN: {0:d})'.format(len(nep2_key)))

        ADDRESS_HASH_SIZE = 4
        ADDRESS_HASH_OFFSET = len(NEP_FLAG) + len(NEP_HEADER)

        try:
            decoded_key = base58.b58decode_check(nep2_key)
        except Exception:
            raise ValueError("Invalid nep2_key")

        address_hash = decoded_key[ADDRESS_HASH_OFFSET:ADDRESS_HASH_OFFSET + ADDRESS_HASH_SIZE]
        encrypted = decoded_key[-32:]

        pwd_normalized = bytes(unicodedata.normalize('NFC', passphrase), 'utf-8')
        derived = scrypt.hash(pwd_normalized, address_hash,
                              N=SCRYPT_ITERATIONS,
                              r=SCRYPT_BLOCKSIZE,
                              p=SCRYPT_PARALLEL_FACTOR,
                              buflen=SCRYPT_KEY_LEN_BYTES)

        derived1 = derived[:32]
        derived2 = derived[32:]

        cipher = AES.new(derived2, AES.MODE_ECB)
        decrypted = cipher.decrypt(encrypted)
        private_key = xor_bytes(decrypted, derived1)

        # Now check that the address hashes match. If they don't, the password was wrong.
        kp_new = KeyPair(priv_key=private_key)
        kp_new_address = kp_new.GetAddress()
        kp_new_address_hash_tmp = hashlib.sha256(kp_new_address.encode("utf-8")).digest()
        kp_new_address_hash_tmp2 = hashlib.sha256(kp_new_address_hash_tmp).digest()
        kp_new_address_hash = kp_new_address_hash_tmp2[:4]
        if (kp_new_address_hash != address_hash):
            raise ValueError("Wrong passphrase")

        return private_key

    def GetAddress(self):
        """
        Returns the public NEO address for this KeyPair

        Returns:
            str: The private key
        """
        script = b'21' + self.PublicKey.encode_point(True) + b'ac'
        script_hash = Crypto.ToScriptHash(script)
        address = Crypto.ToAddress(script_hash)
        return address

    def Export(self):
        """
        Export this KeyPair's private key in WIF format.

        Returns:
            str: The key in wif format
        """
        data = bytearray(38)
        data[0] = 0x80
        data[1:33] = self.PrivateKey[0:32]
        data[33] = 0x01

        checksum = Crypto.Default().Hash256(data[0:34])
        data[34:38] = checksum[0:4]
        b58 = base58.b58encode(bytes(data))

        return b58.decode("utf-8")

    def ExportNEP2(self, passphrase):
        """
        Export the encrypted private key in NEP-2 format.

        Args:
            passphrase (str): The password to encrypt the private key with, as unicode string

        Returns:
            str: The NEP-2 encrypted private key

        Raises:
            ValueError: if the input `passphrase` length is < 2
        """
        if len(passphrase) < 2:
            raise ValueError("Passphrase must have a minimum of 2 characters")

        # Hash address twice, then only use the first 4 bytes
        address_hash_tmp = hashlib.sha256(self.GetAddress().encode("utf-8")).digest()
        address_hash_tmp2 = hashlib.sha256(address_hash_tmp).digest()
        address_hash = address_hash_tmp2[:4]

        # Normalize password and run scrypt over it with the address_hash
        pwd_normalized = bytes(unicodedata.normalize('NFC', passphrase), 'utf-8')
        derived = scrypt.hash(pwd_normalized, address_hash,
                              N=SCRYPT_ITERATIONS,
                              r=SCRYPT_BLOCKSIZE,
                              p=SCRYPT_PARALLEL_FACTOR,
                              buflen=SCRYPT_KEY_LEN_BYTES)

        # Split the scrypt-result into two parts
        derived1 = derived[:32]
        derived2 = derived[32:]

        # Run XOR and encrypt the derived parts with AES
        xor_ed = xor_bytes(bytes(self.PrivateKey), derived1)
        cipher = AES.new(derived2, AES.MODE_ECB)
        encrypted = cipher.encrypt(xor_ed)

        # Assemble the final result
        assembled = bytearray()
        assembled.extend(NEP_HEADER)
        assembled.extend(NEP_FLAG)
        assembled.extend(address_hash)
        assembled.extend(encrypted)

        # Finally, encode with Base58Check
        encrypted_key_nep2 = base58.b58encode_check(bytes(assembled))
        return encrypted_key_nep2.decode("utf-8")
