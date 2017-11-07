from neo.Prompt.Command import Command


class WalletCommand(Command):

    wallet = None

    def __init__(self, *args, **kwargs):
        if 'wallet' in kwargs:
            self.wallet = kwargs.pop('wallet')
        self.prepare(args)

    def prepare(self, args):
        return False

    def execute(self):
        return False