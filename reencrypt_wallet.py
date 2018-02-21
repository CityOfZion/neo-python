from neo.Implementations.Wallets.peewee.PWDatabase import PWDatabase
from neo.Implementations.Wallets.peewee.Models import Key
from neo.Wallets.utils import to_aes_key
from prompt_toolkit import prompt
from Crypto.Cipher import AES
import hashlib
import argparse
import os
from shutil import copyfile


def copy_wallet(path):
    filename = os.path.basename(path)
    directory = os.path.dirname(path)
    if directory:
        new_file_path = '{}/{}{}'.format(directory, 'new_', filename)
    else:
        new_file_path = '{}{}'.format('new_', filename)
    copyfile(path, new_file_path)
    return new_file_path


def LoadStoredData(key):
    print("Looking for key %s " % key)
    try:
        return Key.get(Name=key).Value
    except Exception as e:
        print("Could not get key %s " % e)


def SaveStoredData(key, value):
    k = None
    try:
        k = Key.get(Name=key)
        k.Value = value
    except Exception:
        pass

    if k is None:
        k = Key.create(Name=key, Value=value)

    k.save()


def reset_password(new_path, new_password):
    db = PWDatabase(new_path).DB

    if LoadStoredData('MigrationState') == '1':
        print("This wallet was already secured")
        return False
    else:
        print("The wallet is vulnerable, will proceed with the operation.")

    # Decrypt Master Key - Without using a password
    master_enc = LoadStoredData('MasterKey')
    passwordHash = LoadStoredData('PasswordHash')
    iv = LoadStoredData('IV')

    aes_dec = AES.new(passwordHash, AES.MODE_CBC, iv)
    master_key = aes_dec.decrypt(master_enc)

    # Encrypt again with the new password
    new_key = to_aes_key(new_password)
    new_hash = hashlib.sha256(new_key).digest()

    aes_enc = AES.new(new_key, AES.MODE_CBC, iv)
    mk = aes_enc.encrypt(master_key)
    SaveStoredData('PasswordHash', new_hash)
    SaveStoredData('MasterKey', mk)
    SaveStoredData('MigrationState', '1')
    db.close()
    return True


def main(path):
    if not os.path.exists(path):
        print('Wallet file not found')
        return

    password = prompt("[new password]> ", is_password=True)
    password_confirmation = prompt("[new password again]> ", is_password=True)

    if password != password_confirmation or len(password) < 10:
        print("Please provide matching passwords (>10 characters long)")
        return False

    new_path = copy_wallet(path)
    if reset_password(new_path, password):
        print("A new wallet was created with your master key encrypted with the new password, with the name %s. You can now open this new wallet with the new version of neo-python" % new_path)
    else:
        print("Please remove the newly created file: '{}'".format(new_path))

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Re-encrypts the wallet master-key in a secure way.')
    parser.add_argument('path', help='path to your wallet file')
    args = parser.parse_args()
    main(args.path)
