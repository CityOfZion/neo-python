

def GetBlockchain():
    from neo.Core.Blockchain import Blockchain
    return Blockchain.Default()

def GetGenesis():
    from neo.Core.Blockchain import Blockchain
    return Blockchain.GenesisBlock()

def GetSystemCoin():
    from neo.Core.Blockchain import Blockchain
    return Blockchain.SystemCoin()

def GetSystemShare():
    from neo.Core.Blockchain import Blockchain
    return Blockchain.SystemShare()

def GetConsensusAddress(validators):
    from neo.Core.Blockchain import Blockchain
    return Blockchain.GetConsensusAddress(validators)