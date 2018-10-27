import json
import os
from prompt_toolkit import prompt

from neo.Wallets.utils import to_aes_key
from neo.Prompt.Utils import get_arg
from neo.Implementations.Wallets.peewee.UserWallet import UserWallet
from neo.Prompt.CommandBase import CommandBase, SubCommandBase, CommandDesc
from neo.Prompt.PromptData import PromptData


class CommandCreate(CommandBase):
    def __init__(self):
        super().__init__()

        self.register_sub_command('wallet', CommandCreateWallet)

    def command_desc(self):
        return CommandDesc('create')

    def execute(self, arguments):
        item = get_arg(arguments)

        try:
            self.execute_sub_command(item, arguments[1:])
        except KeyError:
            print(f"Please specify something to create")


class CommandCreateWallet(SubCommandBase):

    @classmethod
    def execute(cls, arguments):
        path = get_arg(arguments, 0)

        if path:
            if os.path.exists(path):
                print("File already exists")
                return

            passwd1 = prompt("[password]> ", is_password=True)
            passwd2 = prompt("[password again]> ", is_password=True)

            if passwd1 != passwd2 or len(passwd1) < 10:
                print("Please provide matching passwords that are at least 10 characters long")
                return

            password_key = to_aes_key(passwd1)

            try:
                PromptData.Wallet = UserWallet.Create(path=path, password=password_key)
                contract = PromptData.Wallet.GetDefaultContract()
                key = PromptData.Wallet.GetKey(contract.PublicKeyHash)
                print("Wallet %s" % json.dumps(PromptData.Wallet.ToJson(), indent=4))
                print("Pubkey %s" % key.PublicKey.encode_point(True))
            except Exception as e:
                print("Exception creating wallet: %s" % e)
                PromptData.Wallet = None
                if os.path.isfile(path):
                    try:
                        os.remove(path)
                    except Exception as e:
                        print("Could not remove {}: {}".format(path, e))
                return

            if PromptData.Wallet:
                PromptData.Prompt.start_wallet_loop()

        else:
            print("Please specify a path")

    @classmethod
    def command_desc(self):
        return CommandDesc('wallet', 'create wallet {path}')
