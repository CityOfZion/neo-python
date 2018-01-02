class VoteState(object):
    PublicKeys = None

    Count = 0

    def __init__(self, keys=None, count=0):
        """
        Create an instance.

        Args:
            keys (EllipticCurve.ECPoint):
            count: number of votes.
        """
        if keys is None:
            self.PublicKeys = []
        else:
            self.PublicKeys = keys

        self.Count = count
