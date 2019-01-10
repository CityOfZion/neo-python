from neo.Prompt.CommandBase import CommandBase, CommandDesc, ParameterDesc
from neo.Prompt import Utils as PromptUtils
from neo.Prompt.PromptData import PromptData
from prompt_toolkit import prompt
from neo.Prompt.PromptPrinter import prompt_print as print


class CommandWalletExport(CommandBase):

    def __init__(self):
        super().__init__()
        self.register_sub_command(CommandWalletExportWIF())
        self.register_sub_command(CommandWalletExportNEP2())

    def command_desc(self):
        return CommandDesc('export', 'export wallet items')

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


class CommandWalletExportWIF(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        wallet = PromptData.Wallet

        if len(arguments) != 1:
            print("Please specify the required parameter")
            return False

        address = arguments[0]
        keys = wallet.GetKeys()
        for key in keys:
            if key.GetAddress() == address:
                passwd = prompt("[wallet password]> ", is_password=True)
                if not wallet.ValidatePassword(passwd):
                    return print("Incorrect password")

                print(f"WIF: {key.Export()}")
                return True
        else:
            print(f"Could not find address {address} in wallet")
            return False

    def command_desc(self):
        p1 = ParameterDesc('address', 'public address in the wallet')
        return CommandDesc('wif', 'export an unprotected private key record of an address', [p1])


class CommandWalletExportNEP2(CommandBase):
    def __init__(self):
        super().__init__()

    def execute(self, arguments):
        wallet = PromptData.Wallet

        if len(arguments) != 1:
            print("Please specify the required parameter")
            return False

        address = arguments[0]

        passphrase = prompt("[key password] ", is_password=True)
        len_pass = len(passphrase)
        if len_pass < 10:
            print(f"Passphrase is too short, length: {len_pass}. Minimum length is 10")
            return False

        passphrase_confirm = prompt("[key password again] ", is_password=True)

        if passphrase != passphrase_confirm:
            print("Please provide matching passwords")
            return False

        keys = wallet.GetKeys()
        for key in keys:
            if key.GetAddress() == address:
                passwd = prompt("[wallet password]> ", is_password=True)
                if not wallet.ValidatePassword(passwd):
                    return print("Incorrect password")

                print(f"NEP2: {key.ExportNEP2(passphrase)}")
                return True
        else:
            print(f"Could not find address {address} in wallet")
            return False

    def command_desc(self):
        p1 = ParameterDesc('address', 'public address in the wallet')
        return CommandDesc('nep2', 'export a passphrase protected private key record of an address (NEP-2 format)', [p1])
