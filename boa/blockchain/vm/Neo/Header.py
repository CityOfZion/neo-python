

class Header():

    @property
    def Hash(self):
        return GetHash(self)

    @property
    def Timestamp(self):
        return GetTimestamp(self)

    @property
    def Version(self):
        return GetVersion(self)

    @property
    def PrevHash(self):
        return GetPrevHash(self)

    @property
    def MerkleRoot(self):
        return GetMerkleRoot(self)

    @property
    def ConsensusData(self):
        return GetConsensusData(self)

    @property
    def NextConsensus(self):
        return GetNextConsensus(self)



def GetHash(header):
    pass

def GetVersion(header):
    pass

def GetPrevHash(header):
    pass

def GetMerkleRoot(header):
    pass

def GetTimestamp(header):
    pass

def GetConsensusData(header):
    pass

def GetNextConsensus(header):
    pass