from neo.Core.TX.Transaction import *
from neocore.Fixed8 import Fixed8
from neo.Core.Blockchain import Blockchain
from neo.Core.CoinReference import CoinReference


class ClaimTransaction(Transaction):
    Claims = set()

    def Size(self):
        """
        Get the total size in bytes of the object.

        Returns:
            int: size.
        """
        return super(ClaimTransaction, self).Size() + sys.getsizeof(self.Claims)

    def __init__(self, *args, **kwargs):
        """
        Create an instance.

        Args:
            *args:
            **kwargs:
        """
        super(ClaimTransaction, self).__init__(*args, **kwargs)

        self.Type = TransactionType.ClaimTransaction

    def NetworkFee(self):
        """
        Get the network fee for a claim transaction.

        Returns:
            Fixed8: currently fixed to 0.
        """
        return Fixed8(0)

    def DeserializeExclusiveData(self, reader):
        """
        Deserialize full object.

        Args:
            reader (neo.IO.BinaryReader):

        Raises:
            Exception: If the transaction type is incorrect or if there are no claims.
        """
        self.Type = TransactionType.ClaimTransaction
        if self.Version != 0:
            raise Exception('Format Exception')

        numrefs = reader.ReadVarInt()

        claims = []
        for i in range(0, numrefs):
            c = CoinReference()
            c.Deserialize(reader)
            claims.append(c)

        self.Claims = claims
        if len(self.Claims) == 0:
            raise Exception('Format Exception')

    def GetScriptHashesForVerifying(self):
        """
        Get a list of script hashes for verifying transactions.

        Raises:
            Exception: if there are no valid transactions to claim from.

        Returns:
            list: of UInt160 type script hashes.
        """
        hashes = super(ClaimTransaction, self).GetScriptHashesForVerifying()

        for hash, group in groupby(self.Claims, lambda x: x.PrevHash):
            tx, height = Blockchain.Default().GetTransaction(hash)

            if tx is None:
                raise Exception("Invalid Claim Operation")

            for claim in group:
                if len(tx.outputs) <= claim.PrevIndex:
                    raise Exception("Invalid Claim Operation")

                script_hash = tx.outputs[claim.PrevIndex].ScriptHash

                if script_hash not in hashes:
                    hashes.append(script_hash)

        hashes.sort()

        return hashes

    def SerializeExclusiveData(self, writer):
        """
        Serialize object.

        Args:
            writer (neo.IO.BinaryWriter):
        """
        writer.WriteSerializableArray(self.Claims)

    def ToJson(self):
        """
        Convert object members to a dictionary that can be parsed as JSON.

        Returns:
             dict:
        """
        json = super(ClaimTransaction, self).ToJson()

        json['claims'] = [claim.ToJson() for claim in self.Claims]

        return json

    def Verify(self, mempool):
        """
        Verify the transaction.

        Args:
            mempool:

        Returns:
            bool: True if verified. False otherwise.
        """
        if not super(ClaimTransaction, self).Verify(mempool):
            return False

        # wat does this do
        # get all claim transactinos from mempool list
        # that are not this claim
        # and gather all the claims of those claim transactions
        # and see if they intersect the claims of this transaction
        # and if that number is greater than zero that we do not verify
        # (now, to do that in python)
        # if (mempool.OfType < ClaimTransaction > ().Where(p => p != this).SelectMany(p= > p.Claims).Intersect(Claims).Count() > 0)
        # return false;

        # im sorry about the below
        otherclaimTxs = [tx for tx in mempool if tx is ClaimTransaction and tx is not self]
        for other in otherclaimTxs:
            # check to see if the length of the intersection between this objects claim's and the other txs claims is > 0
            if len([list(filter(lambda x: x in self.Claims, otherClaims)) for otherClaims in other.Claims]):
                return False

        txResult = None
        for tx in self.GetTransactionResults():
            if tx.AssetId == Blockchain.SystemCoin().Hash:
                txResult = tx
                break

        if txResult is None or txResult.Amount > Fixed8(0):
            return False

        try:
            return Blockchain.CalculateBonusIgnoreClaimed(self.Claims, False) == -txResult.Amount

        except Exception as e:
            logger.error('Could not calculate bonus: %s ' % e)

        return False
