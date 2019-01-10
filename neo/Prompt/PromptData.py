class PromptData:
    Prompt = None
    Wallet = None

    @staticmethod
    def close_wallet():
        if not PromptData.Wallet:
            return False

        path = PromptData.Wallet._path
        PromptData.Prompt.stop_wallet_loop()
        PromptData.Wallet.Close()
        PromptData.Wallet = None
        print("Closed wallet %s" % path)
        return True
