import argparse
from neo.Wallets.utils import to_aes_key
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from prompt_toolkit import prompt
from neo.Core.Helper import Helper
from neocore.KeyPair import KeyPair
from neo.SmartContract.Contract import Contract
from neocore.Cryptography.Crypto import Crypto


def main():
    parser = argparse.ArgumentParser(description='A utility for signing messages.  Example usage: "np-sign mymessage --wallet_file path/to/my/wallet" or use an NEP2 key/passphrase like "np-sign mymessage -n"')
    parser.add_argument('message', type=str, help='The message in string format to be signed')
    parser.add_argument('-w', '--wallet_file', type=str, default=None, help='If using a wallet file, the path to the wallet file')
    parser.add_argument('-a', '--address', type=str, default=False, help='If using a wallet file with more than 1 address, the address you would like to use.  Otherwise the default address will be used')
    parser.add_argument('-n', '--nep2', action='store_true', help="Whether to use an NEP2 passhrase rather than a wallet")
    parser.add_argument('--wif', type=str, default=None, help='If using a wif pass in the wif')
    args = parser.parse_args()
    try:

        if args.wallet_file:

            passwd = prompt('[Wallet password]> ', is_password=True)
            wallet = UserWallet.Open(args.wallet_file, to_aes_key(passwd))

            contract = wallet.GetDefaultContract()
            if args.address:
                addr = args.address
                script_hash = Helper.AddrStrToScriptHash(addr)
                contract = wallet.GetContract(script_hash)

                if contract is None:
                    raise Exception('Address %s not found in wallet %s ' % (addr, args.wallet_file))

            print("Signing With Address %s " % contract.Address)
            signature, pubkey = wallet.SignMessage(args.message, contract.ScriptHash)

            pubkey = pubkey.encode_point().decode('utf-8')
            signature = signature.hex()
            print("pubkey, sig: %s %s " % (pubkey, signature))

        elif args.nep2:

            nep2_key = prompt('[nep2 key]> ', is_password=True)
            nep2_passwd = prompt("[nep2 key password]> ", is_password=True)

            prikey = KeyPair.PrivateKeyFromNEP2(nep2_key, nep2_passwd)
            keypair = KeyPair(priv_key=prikey)
            contract = Contract.CreateSignatureContract(keypair.PublicKey)
            print("Signing With Address %s " % contract.Address)
            signature = Crypto.Sign(args.message, prikey)

            pubkey = keypair.PublicKey.encode_point().decode('utf-8')
            signature = signature.hex()
            print("pubkey, sig: %s %s " % (pubkey, signature))

        elif args.wif:
            prikey = KeyPair.PrivateKeyFromWIF(args.wif)
            keypair = KeyPair(priv_key=prikey)
            contract = Contract.CreateSignatureContract(keypair.PublicKey)
            print("Signing With Address %s " % contract.Address)
            signature = Crypto.Sign(args.message, prikey)

            pubkey = keypair.PublicKey.encode_point().decode('utf-8')
            signature = signature.hex()
            print("pubkey, sig: %s %s " % (pubkey, signature))

    except Exception as e:
        print("Could not sign: %s " % e)


if __name__ == "__main__":
    main()
