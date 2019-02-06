import binascii
import json
from neo.Prompt.CommandBase import CommandBase, CommandDesc, ParameterDesc
from neo.Prompt.PromptData import PromptData
from neo.Prompt.Commands.LoadSmartContract import ImportContractAddr
from neo.Prompt import Utils as PromptUtils
from neocore.KeyPair import KeyPair
from prompt_toolkit import prompt
from neocore.Utils import isValidPublicAddress
from neocore.UInt160 import UInt160
from neocore.Cryptography.Crypto import Crypto
from neo.SmartContract.Contract import Contract
from neo.Core.Blockchain import Blockchain
from neo.Wallets import NEP5Token
from neo.Prompt.PromptPrinter import prompt_print as print


class CommandWalletImport(CommandBase):

    def __init__(self):
        super().__init__()
        self.register_sub_command(CommandWalletImportWIF())
        self.register_sub_command(CommandWalletImportNEP2())
        self.register_sub_command(CommandWalletImportWatchAddr())
        self.register_sub_command(CommandWalletImportMultisigAddr())
        self.register_sub_command(CommandWalletImportToken())
        self.register_sub_command(CommandWalletImportContractAddr())

    def command_desc(self):
        return CommandDesc('import', 'import wallet items')

    def execute(self, arguments):
        item = PromptUtils.get_arg(arguments)

        if not item:
            print(f"run `{self.command_desc().command} help` to see supported queries")
            return False

        try:
            return self.execute_sub_command(item, arguments[1:])
        except KeyError:
            print(f"{item} is an invalid parameter")
            return False


class CommandWalletImportWIF(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        wallet = PromptData.Wallet

        if len(arguments) != 1:
            print("Please specify the required parameter")
            return False

        wif = arguments[0]
        try:
            kp = KeyPair.PrivateKeyFromWIF(wif)
        except ValueError as e:
            print(f"WIF Error: {str(e)}")
            return False

        try:
            key = wallet.CreateKey(kp)
            print(f"Imported key: {wif}")
            pub_key = key.PublicKey.encode_point(True).decode('utf-8')
            print(f"Pubkey: {pub_key}")
            print(f"Address: {key.GetAddress()}")

        except Exception as e:
            # couldn't find an exact call that throws this but it was in the old code. Leaving it in for now.
            print(f"Key creation error: {str(e)}")
            return False

        return True

    def command_desc(self):
        p1 = ParameterDesc('key', 'private key record in WIF format')
        return CommandDesc('wif', 'import an unprotected private key record of an address', [p1])


class CommandWalletImportNEP2(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        wallet = PromptData.Wallet

        if len(arguments) != 1:
            print("Please specify the required parameter")
            return False

        nep2_key = arguments[0]
        passphrase = prompt("[key password] ", is_password=True)

        try:
            kp = KeyPair.PrivateKeyFromNEP2(nep2_key, passphrase)
        except ValueError as e:
            print(str(e))
            return False

        try:
            key = wallet.CreateKey(kp)
            print(f"Imported key: {nep2_key}")
            pub_key = key.PublicKey.encode_point(True).decode('utf-8')
            print(f"Pubkey: {pub_key}")
            print(f"Address: {key.GetAddress()}")

        except Exception as e:
            # couldn't find an exact call that throws this but it was in the old code. Leaving it in for now.
            print(f"Key creation error: {str(e)}")
            return False

    def command_desc(self):
        p1 = ParameterDesc('private key', 'NEP-2 protected private key')
        return CommandDesc('nep2', 'import a passphrase protected private key record (NEP-2 format)', [p1])


class CommandWalletImportWatchAddr(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        wallet = PromptData.Wallet

        if len(arguments) != 1:
            print("Please specify the required parameter")
            return False

        addr = arguments[0]
        if not isValidPublicAddress(addr):
            print("Invalid address specified")
            return False

        try:
            addr_script_hash = wallet.ToScriptHash(addr)
            wallet.AddWatchOnly(addr_script_hash)
        except ValueError as e:
            print(str(e))
            return False

        print(f"Added address {addr} as watch-only")
        return True

    def command_desc(self):
        p1 = ParameterDesc('address', 'public NEO address to watch')
        return CommandDesc('watch_addr', 'import a public address as watch only', [p1])


class CommandWalletImportMultisigAddr(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        wallet = PromptData.Wallet

        if len(arguments) < 3:
            print("Please specify the minimum required parameters")
            return False

        pubkey_in_wallet = arguments[0]
        if not PromptUtils.is_valid_public_key(pubkey_in_wallet):
            print("Invalid public key format")
            return False

        key_script_hash = Crypto.ToScriptHash(pubkey_in_wallet, unhex=True)
        if not wallet.ContainsKeyHash(key_script_hash):
            print("Supplied first public key does not exist in own wallet.")
            return False

        try:
            min_signature_cnt = int(arguments[1])
        except ValueError:
            print(f"Invalid minimum signature count value: {arguments[1]}")
            return False

        if min_signature_cnt < 1:
            print("Minimum signatures count cannot be lower than 1")
            return False

        # validate minimum required signing key count
        signing_keys = arguments[2:]
        signing_keys.append(pubkey_in_wallet)
        len_signing_keys = len(signing_keys)
        if len_signing_keys < min_signature_cnt:
            # we need at least 2 public keys in total otherwise it's just a regular address.
            # 1 pub key is from an address in our own wallet, a secondary key can come from any place.
            print(f"Missing remaining signing keys. Minimum required: {min_signature_cnt} given: {len_signing_keys}")
            return False

        # validate remaining pub keys
        for key in signing_keys:
            if not PromptUtils.is_valid_public_key(key):
                print(f"Invalid signing key {key}")
                return False

        # validate that all signing keys are unique
        if len(signing_keys) > len(set(signing_keys)):
            print("Provided signing keys are not unique")
            return False

        verification_contract = Contract.CreateMultiSigContract(key_script_hash, min_signature_cnt, signing_keys)
        address = verification_contract.Address
        wallet.AddContract(verification_contract)
        print(f"Added multi-sig contract address {address} to wallet")
        return True

    def command_desc(self):
        p1 = ParameterDesc('own pub key', 'public key in your own wallet (use `wallet` to find the information)')
        p2 = ParameterDesc('sign_cnt', 'minimum number of signatures required for using the address (min is: 1)')
        p3 = ParameterDesc('signing key n', 'all remaining signing public keys')
        return CommandDesc('multisig_addr', 'import a multi-signature address', [p1, p2, p3])


class CommandWalletImportToken(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        if len(arguments) != 1:
            print("Please specify the required parameter")
            return

        try:
            contract_hash = UInt160.ParseString(arguments[0]).ToBytes()
        except Exception:
            print(f"Invalid contract hash: {arguments[0]}")
            return

        return ImportToken(PromptData.Wallet, contract_hash)

    def command_desc(self):
        p1 = ParameterDesc('contract_hash', 'token script hash')
        return CommandDesc('token', 'import a token', [p1])


class CommandWalletImportContractAddr(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        wallet = PromptData.Wallet

        if len(arguments) != 2:
            print("Please specify the required parameters")
            return

        try:
            contract_hash = UInt160.ParseString(arguments[0]).ToBytes()
        except Exception:
            print(f"Invalid contract hash: {arguments[0]}")
            return

        pubkey = arguments[1]
        if not PromptUtils.is_valid_public_key(pubkey):
            print(f"Invalid pubkey: {arguments[1]}")
            return

        pubkey_script_hash = Crypto.ToScriptHash(pubkey, unhex=True)

        return ImportContractAddr(wallet, contract_hash, pubkey_script_hash)

    def command_desc(self):
        p1 = ParameterDesc('contract_hash', 'contract script hash')
        p2 = ParameterDesc('pubkey', 'pubkey of the contract')
        return CommandDesc('contract_addr', 'import a contract address', [p1, p2])


def ImportToken(wallet, contract_hash):
    if wallet is None:
        print("please open a wallet")
        return

    contract = Blockchain.Default().GetContract(contract_hash)

    if contract:
        hex_script = binascii.hexlify(contract.Code.Script)
        token = NEP5Token.NEP5Token(script=hex_script)

        result = token.Query()

        if result:
            wallet.AddNEP5Token(token)
            print("added token %s " % json.dumps(token.ToJson(), indent=4))
            return token
        else:
            print("Could not import token")
    else:
        print("Could not find the contract hash")
