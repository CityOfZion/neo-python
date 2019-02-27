from neo.Core.Blockchain import Blockchain


class PromptData:
    Prompt = None
    Wallet = None

    @staticmethod
    def close_wallet():
        if not PromptData.Wallet:
            return False

        path = PromptData.Wallet._path
        Blockchain.Default().PersistCompleted.on_change -= PromptData.Wallet.ProcessNewBlock
        PromptData.Wallet.Close()
        PromptData.Wallet = None
        print("Closed wallet %s" % path)
        return True
