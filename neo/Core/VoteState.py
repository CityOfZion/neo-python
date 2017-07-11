

class VoteState(object):

    PublicKeys=[]

    Count = 0

    def __init__(self, keys=[], count=0):
        self.PublicKeys = keys
        self.Count = count