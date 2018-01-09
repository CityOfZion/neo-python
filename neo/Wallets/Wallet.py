# -*- coding:utf-8 -*-
"""
Description:
    Wallet
Usage:
    from neo.Wallets.Wallet import Wallet
"""
import traceback
from itertools import groupby
from base58 import b58decode
from decimal import Decimal
from Crypto import Random
from Crypto.Cipher import AES
from logzero import logger

from neo.Core.TX.Transaction import TransactionType, TransactionOutput
from neo.Core.State.CoinState import CoinState
from neo.Core.Blockchain import Blockchain
from neo.Core.CoinReference import CoinReference
from neo.Core.TX.ClaimTransaction import ClaimTransaction
from neocore.Cryptography.Helper import *
from neocore.Cryptography.Crypto import Crypto
from neo.Wallets.AddressState import AddressState
from neo.Wallets.Coin import Coin
from neocore.KeyPair import KeyPair
from neo.Wallets.NEP5Token import NEP5Token
from neo.Settings import settings
from neo.Implementations.Blockchains.LevelDB.LevelDBBlockchain import LevelDBBlockchain
from neocore.Fixed8 import Fixed8
from neocore.UInt160 import UInt160
from neocore.UInt256 import UInt256
from neo.Core.Helper import Helper


class Wallet(object):
    AddressVersion = None

    _path = ''
    _iv = None
    _master_key = None
    _keys = {}  # holds keypairs
    _contracts = {}  # holds Contracts
    _tokens = {}  # holds references to NEP5 tokens
    _watch_only = []  # holds set of hashes
    _coins = {}  # holds Coin References

    _current_height = 0

    _db_path = _path

    _indexedDB = None

    _vin_exclude = None

    @property
    def WalletHeight(self):
        return self._current_height

    """docstring for Wallet"""

    def __init__(self, path, passwordKey, create):
        """

        Args:
            path (str): A path indicating where to create or open the wallet.
            passwordKey (str): A password to use in creating or opening the wallet.
            create (bool): Whether to create the wallet or simply open.
        """

        self.AddressVersion = settings.ADDRESS_VERSION
        self._path = path

        if create:
            self._iv = bytes(Random.get_random_bytes(16))
            self._master_key = bytes(Random.get_random_bytes(32))
            self._keys = {}
            self._contracts = {}
            self._coins = {}

            if Blockchain.Default() is None:
                self._indexedDB = LevelDBBlockchain(settings.LEVELDB_PATH)
                Blockchain.RegisterBlockchain(self._indexedDB)
            else:
                self._indexedDB = Blockchain.Default()

            self._current_height = 0

            self.BuildDatabase()

            passwordHash = hashlib.sha256(passwordKey.encode('utf-8')).digest()
            master = AES.new(passwordHash, AES.MODE_CBC, self._iv)
            mk = master.encrypt(self._master_key)
            self.SaveStoredData('PasswordHash', passwordHash)
            self.SaveStoredData('IV', self._iv),
            self.SaveStoredData('MasterKey', mk)

            self.SaveStoredData('Height', self._current_height.to_bytes(4, 'little'))

        else:
            self.BuildDatabase()

            passwordHash = self.LoadStoredData('PasswordHash')
            if passwordHash is None:
                raise Exception("Password hash not found in database")

            hkey = hashlib.sha256(passwordKey.encode('utf-8'))

            if passwordHash is not None and passwordHash != hashlib.sha256(passwordKey.encode('utf-8')).digest():
                raise Exception("Incorrect Password")

            self._iv = self.LoadStoredData('IV')
            master_stored = self.LoadStoredData('MasterKey')
            aes = AES.new(hkey.digest(), AES.MODE_CBC, self._iv)
            self._master_key = aes.decrypt(master_stored)

            self._keys = self.LoadKeyPairs()
            self._contracts = self.LoadContracts()
            self._watch_only = self.LoadWatchOnly()
            self._tokens = self.LoadNEP5Tokens()
            self._coins = self.LoadCoins()
            try:
                h = int(self.LoadStoredData('Height'))
                self._current_height = h
            except Exception as e:
                logger.error("Could not load height data %s " % e)
                self._current_height = 0

            del passwordKey

    def BuildDatabase(self):
        # abstract
        pass

    def AddContract(self, contract):
        """
        Add a contract to the wallet.

        Args:
            contract (Contract): a contract of type neo.SmartContract.Contract.

        Raises:
            Exception: Invalid operation - public key mismatch.
        """
        if not contract.PublicKeyHash.ToBytes() in self._keys.keys():
            raise Exception('Invalid operation - public key mismatch')

        self._contracts[contract.ScriptHash.ToBytes()] = contract
        if contract.ScriptHash in self._watch_only:
            self._watch_only.remove(contract.ScriptHash)

    def AddWatchOnly(self, script_hash):
        """
        Add a watch only address to the wallet.

        Args:
            script_hash (UInt160): a bytearray (len 20) representing the public key.

        Note:
            Prints a warning to the console if the address already exists in the wallet.
        """
        if script_hash in self._contracts:
            logger.error("Address already in contracts")
            return

        self._watch_only.append(script_hash)

    def AddNEP5Token(self, token):
        """
        Add a NEP-5 compliant token to the wallet.

        Args:
            token (NEP5Token): an instance of type neo.Wallets.NEP5Token.

        Note:
            Prints a warning to the console if the token already exists in the wallet.
        """
        if token.ScriptHash.ToBytes() in self._tokens.keys():
            logger.error("Token already in wallet")
            return
        self._tokens[token.ScriptHash.ToBytes()] = token

    def DeleteNEP5Token(self, token):
        """
        Delete a NEP5 token from the wallet.

        Args:
            token (NEP5Token): an instance of type neo.Wallets.NEP5Token.

        Returns:
            bool: success status.
        """
        return self._tokens.pop(token.ScriptHash.ToBytes())

    def ChangePassword(self, password_old, password_new):
        """
        Change the password used to protect the private key.

        Args:
            password_old (str): the current password used to encrypt the private key.
            password_new (str): the new to be used password to encrypt the private key.

        Returns:
            bool: whether the password has been changed
        """
        if not self.ValidatePassword(password_old):
            return False

        if isinstance(password_new, str):
            password_new = password_new.encode('utf-8')

        password_key = hashlib.sha256(password_new)
        self.SaveStoredData("PasswordHash", password_key)
        self.SaveStoredData("MasterKey", AES.new(self._master_key, AES.MODE_CBC, self._iv))

        return True

    def ContainsKey(self, public_key):
        """
        Test if the wallet contains the supplied public key.

        Args:
            public_key (edcsa.Curve.point): a public key to test for its existance. i.e. KeyPair.PublicKey

        Returns:
            bool: True if exists, False otherwise.
        """
        return self.ContainsKeyHash(Crypto.ToScriptHash(public_key.encode_point(True), unhex=True))

    def ContainsKeyHash(self, public_key_hash):
        """
        Test if the wallet contains the supplied public key hash in its key list.

        Args:
            public_key_hash (UInt160): a public key hash to test for its existance.

        Returns:
            bool: True if exists in wallet key list, False otherwise.
        """
        return public_key_hash.ToBytes() in self._keys.keys()

    def ContainsAddress(self, script_hash):
        """
        Determine if the wallet contains the address.

        Args:
            script_hash (UInt160): a bytearray (len 20) representing the public key.

        Returns:
            bool: True, if the address is present in the wallet. False otherwise.
        """
        return self.CheckAddressState(script_hash) >= AddressState.InWallet

    def ContainsAddressStr(self, address):
        """
        Determine if the wallet contains the address.

        Args:
            address (str): a string representing the public key.

        Returns:
            bool: True, if the address is present in the wallet. False otherwise.
        """
        for key, contract in self._contracts.items():
            if contract.Address == address:
                return True
        return False

    def CreateKey(self, private_key=None):
        """
        Create a KeyPair

        Args:
            private_key (iterable_of_ints): (optional) 32 byte private key

        Returns:
            KeyPair: a KeyPair instance
        """
        if private_key is None:
            private_key = bytes(Random.get_random_bytes(32))

        key = KeyPair(priv_key=private_key)
        self._keys[key.PublicKeyHash.ToBytes()] = key
        return key

    def EncryptPrivateKey(self, decrypted):
        """
        Encrypt the provided plaintext with the initialized private key.

        Args:
            decrypted (byte string): the plaintext to be encrypted.

        Returns:
            bytes: the ciphertext.
        """
        aes = AES.new(self._master_key, AES.MODE_CBC, self._iv)
        return aes.encrypt(decrypted)

    def DecryptPrivateKey(self, encrypted_private_key):
        """
        Decrypt the provided ciphertext with the initialized private key.

        Args:
            encrypted_private_key (byte string): the ciphertext to be decrypted.

        Returns:
            bytes: the ciphertext.
        """
        aes = AES.new(self._master_key, AES.MODE_CBC, self._iv)
        return aes.decrypt(encrypted_private_key)

    def DeleteKey(self, public_key_hash):
        raise NotImplementedError()

    def DeleteAddress(self, script_hash):
        """
        Deletes an address from the wallet (includes watch-only addresses).

        Args:
            script_hash (UInt160): a bytearray (len 20) representing the public key.

        Returns:
            tuple:
                bool: True if address removed, False otherwise.
                list: a list of any ``neo.Wallet.Coin`` objects to be removed from the wallet.
        """
        coin_keys_toremove = []
        coins_to_remove = []
        for key, coinref in self._coins.items():
            if coinref.Output.ScriptHash.ToBytes() == script_hash.ToBytes():
                coin_keys_toremove.append(key)
                coins_to_remove.append(coinref)

        for k in coin_keys_toremove:
            del self._coins[k]

        ok = False
        if script_hash.ToBytes() in self._contracts.keys():
            ok = True
            del self._contracts[script_hash.ToBytes()]
        elif script_hash in self._watch_only:
            ok = True
            self._watch_only.remove(script_hash)

        return ok, coins_to_remove

    def FindCoinsByVins(self, vins):
        """
        Looks through the current collection of coins in a wallet
        and chooses coins that match the specified CoinReference objects.

        Args:
            vins: A list of ``neo.Core.CoinReference`` objects.

        Returns:
            list: A list of ``neo.Wallet.Coin`` objects.
        """
        ret = []
        for coin in self.GetCoins():
            coinref = coin.Reference
            for vin in vins:
                if coinref.PrevIndex == vin.PrevIndex and \
                        coinref.PrevHash == vin.PrevHash:
                    ret.append(coin)
        return ret

    def FindUnspentCoins(self, from_addr=None, use_standard=False, watch_only_val=0):
        """
        Finds unspent coin objects in the wallet.

        Args:
            from_addr (UInt160): a bytearray (len 20) representing an address.
            use_standard (bool): whether or not to only include standard contracts ( i.e not a smart contract addr ).
            watch_only_val (int): a flag ( 0 or 64 ) indicating whether or not to find coins that are in 'watch only' addresses.

        Returns:
            list: a list of ``neo.Wallet.Coins`` in the wallet that are not spent.
        """
        ret = []
        for coin in self.GetCoins():
            if coin.State & CoinState.Confirmed > 0 and \
                    coin.State & CoinState.Spent == 0 and \
                    coin.State & CoinState.Locked == 0 and \
                    coin.State & CoinState.Frozen == 0 and \
                    coin.State & CoinState.WatchOnly == watch_only_val:

                do_exclude = False
                if self._vin_exclude:
                    for to_exclude in self._vin_exclude:

                        if coin.Reference.PrevIndex == to_exclude.PrevIndex and \
                                coin.Reference.PrevHash == to_exclude.PrevHash:
                            do_exclude = True

                if do_exclude:
                    continue

                if from_addr is not None:
                    if coin.Output.ScriptHash == from_addr:
                        ret.append(coin)
                elif use_standard:

                    contract = self._contracts[coin.Output.ScriptHash.ToBytes()]
                    if contract.IsStandard:
                        ret.append(coin)
                else:
                    ret.append(coin)

        return ret

    def FindUnspentCoinsByAsset(self, asset_id, from_addr=None, use_standard=False, watch_only_val=0):
        """
        Finds unspent coin objects in the wallet limited to those of a certain asset type.

        Args:
            asset_id (UInt256): a bytearray (len 32) representing an asset on the blockchain.
            from_addr (UInt160): a bytearray (len 20) representing an address.
            use_standard (bool): whether or not to only include standard contracts ( i.e not a smart contract addr ).
            watch_only_val (int): a flag ( 0 or 64 ) indicating whether or not to find coins that are in 'watch only' addresses.

        Returns:
            list: a list of ``neo.Wallet.Coin`` in the wallet that are not spent
        """
        coins = self.FindUnspentCoins(from_addr=from_addr, use_standard=use_standard, watch_only_val=watch_only_val)

        return [coin for coin in coins if coin.Output.AssetId == asset_id]

    def FindUnspentCoinsByAssetAndTotal(self, asset_id, amount, from_addr=None, use_standard=False, watch_only_val=0, reverse=False):
        """
        Finds unspent coin objects totalling a requested value in the wallet limited to those of a certain asset type.

        Args:
            asset_id (UInt256): a bytearray (len 32) representing an asset on the blockchain.
            amount (int): the amount of unspent coins that are being requested.
            from_addr (UInt160): a bytearray (len 20) representing an address.
            use_standard (bool): whether or not to only include standard contracts ( i.e not a smart contract addr ).
            watch_only_val (int): a flag ( 0 or 64 ) indicating whether or not to find coins that are in 'watch only' addresses.

        Returns:
            list: a list of ``neo.Wallet.Coin`` in the wallet that are not spent. this list is empty if there are not enough coins to satisfy the request.
        """
        coins = self.FindUnspentCoinsByAsset(asset_id, from_addr=from_addr,
                                             use_standard=use_standard, watch_only_val=watch_only_val)

        sum = Fixed8(0)

        for coin in coins:
            sum = sum + coin.Output.Value

        if sum < amount:
            return None

        coins = sorted(coins, key=lambda coin: coin.Output.Value.value)

        if reverse:
            coins.reverse()

        total = Fixed8(0)

        # go through all coins, see if one is an exact match. then we'll use that
        for coin in coins:
            if coin.Output.Value == amount:
                return [coin]

        to_ret = []
        for coin in coins:
            total = total + coin.Output.Value
            to_ret.append(coin)
            if total >= amount:
                break

        return to_ret

    def GetUnclaimedCoins(self):
        """
        Gets coins in the wallet that have not been 'claimed', or redeemed for their gas value on the blockchain.

        Returns:
            list: a list of ``neo.Wallet.Coin`` that have 'claimable' value
        """
        unclaimed = []

        neo = Blockchain.SystemShare().Hash

        for coin in self.GetCoins():
            if coin.Output.AssetId == neo and \
                    coin.State & CoinState.Confirmed > 0 and \
                    coin.State & CoinState.Spent > 0 and \
                    coin.State & CoinState.Claimed == 0 and \
                    coin.State & CoinState.Frozen == 0 and \
                    coin.State & CoinState.WatchOnly == 0:
                unclaimed.append(coin)

        return unclaimed

    def GetAvailableClaimTotal(self):
        """
        Gets the total amount of Gas that this wallet is able to claim at a given moment.

        Returns:
            Fixed8: the amount of Gas available to claim as a Fixed8 number.
        """
        coinrefs = [coin.Reference for coin in self.GetUnclaimedCoins()]
        bonus = Blockchain.CalculateBonusIgnoreClaimed(coinrefs, True)
        return bonus

    def GetUnavailableBonus(self):
        """
        Gets the total claimable amount of Gas in the wallet that is not available to claim
        because it has not yet been spent.

        Returns:
            Fixed8: the amount of Gas unavailable to claim.
        """
        height = Blockchain.Default().Height + 1
        unspents = self.FindUnspentCoinsByAsset(Blockchain.SystemShare().Hash)
        refs = [coin.Reference for coin in unspents]
        try:
            unavailable_bonus = Blockchain.CalculateBonus(refs, height_end=height)
            return unavailable_bonus
        except Exception as e:
            pass
        return Fixed8(0)

    def GetKey(self, public_key_hash):
        """
        Get the KeyPair belonging to the public key hash.

        Args:
            public_key_hash (UInt160): a public key hash to get the KeyPair for.

        Returns:
            KeyPair: If successful, the KeyPair belonging to the public key hash, otherwise None
        """
        if public_key_hash.ToBytes() in self._keys.keys():
            return self._keys[public_key_hash.ToBytes()]
        return None

    def GetKeyByScriptHash(self, script_hash):
        """
        Get the KeyPair belonging to the script hash.

        Args:
            script_hash (UInt160): a bytearray (len 20) representing the public key.

        Returns:
            KeyPair: If successful, the KeyPair belonging to the public key hash, otherwise None
        """
        contract = self.GetContract(script_hash)
        if contract:
            return self.GetKey(contract.PublicKeyHash)
        return None

    def GetAvailable(self, asset_id):
        raise NotImplementedError()

    def GetTokens(self):
        return self._tokens

    def GetTokenBalance(self, token, watch_only=0):
        """
        Get the balance of the specified token.

        Args:
            token (NEP5Token): an instance of type neo.Wallets.NEP5Token to get the balance from.
            watch_only (bool): True, to limit to watch only wallets.

        Returns:
            Decimal: total balance for `token`.
        """
        total = Decimal(0)

        if watch_only > 0:
            for addr in self._watch_only:
                balance = token.GetBalance(self, addr)
                total += balance
        else:
            for contract in self._contracts.values():
                balance = token.GetBalance(self, contract.Address)
                total += balance
        return total

    def GetBalance(self, asset_id, watch_only=0):
        """
        Get the balance of a specific token by its asset id.

        Args:
            asset_id (NEP5Token|TransactionOutput): an instance of type neo.Wallets.NEP5Token or neo.Core.TX.Transaction.TransactionOutput to get the balance from.
            watch_only (bool): True, to limit to watch only wallets.

        Returns:
            Fixed8: total balance.
        """
        total = Fixed8(0)

        if type(asset_id) is NEP5Token:
            return self.GetTokenBalance(asset_id, watch_only)

        for coin in self.GetCoins():
            if coin.Output.AssetId == asset_id:
                if coin.State & CoinState.Confirmed > 0 and \
                        coin.State & CoinState.Spent == 0 and \
                        coin.State & CoinState.Locked == 0 and \
                        coin.State & CoinState.Frozen == 0 and \
                        coin.State & CoinState.WatchOnly == watch_only:
                    total = total + coin.Output.Value

        return total

    def SaveStoredData(self, key, value):
        # abstract
        pass

    def LoadStoredData(self, key):
        # abstract
        pass

    def LoadKeyPairs(self):
        # abstract
        pass

    def LoadContracts(self):
        # abstract
        pass

    def LoadWatchOnly(self):
        # abstract
        pass

    def LoadCoins(self):
        # abstract
        pass

    def LoadNEP5Tokens(self):
        # abstract
        pass

    def ProcessBlocks(self):
        """
        Method called on a loop to check the current height of the blockchain.  If the height of the blockchain
        is more than the current stored height in the wallet, we get the next block in line and
        processes it.

        In the case that the wallet height is far behind the height of the blockchain, we do this 500
        blocks at a time.
        """
        blockcount = 0
        while self._current_height <= Blockchain.Default().Height and blockcount < 500:

            block = Blockchain.Default().GetBlockByHeight(self._current_height)

            if block is not None:
                self.ProcessNewBlock(block)

            blockcount += 1

        self.SaveStoredData("Height", self._current_height)

    def ProcessNewBlock(self, block):
        """
        Processes a block on the blockchain.  This should be done in a sequential order, ie block 4 should be
        only processed after block 3.

        Args:
            block: (neo.Core.Block) a block on the blockchain.
        """
        added = set()
        changed = set()
        deleted = set()

        try:
            # go through the list of transactions in the block and enumerate
            # over their outputs
            for tx in block.FullTransactions:

                for index, output in enumerate(tx.outputs):

                    # check to see if the outputs in the tx are in this wallet
                    state = self.CheckAddressState(output.ScriptHash)

                    if state & AddressState.InWallet > 0:

                        # if its in the wallet, check to see if the coin exists yet

                        key = CoinReference(tx.Hash, index)

                        # if it exists, update it, otherwise create a new one
                        if key in self._coins.keys():
                            coin = self._coins[key]
                            coin.State |= CoinState.Confirmed
                            changed.add(coin)
                        else:
                            newcoin = Coin.CoinFromRef(coin_ref=key, tx_output=output, state=CoinState.Confirmed)
                            self._coins[key] = newcoin
                            added.add(newcoin)

                        if state & AddressState.WatchOnly > 0:
                            self._coins[key].State |= CoinState.WatchOnly
                            changed.add(self._coins[key])

            # now iterate over the inputs of the tx and do the same
            for tx in block.FullTransactions:

                for input in tx.inputs:

                    if input in self._coins.keys():
                        if self._coins[input].Output.AssetId == Blockchain.SystemShare().Hash:
                            coin = self._coins[input]
                            coin.State |= CoinState.Spent | CoinState.Confirmed
                            changed.add(coin)

                        else:
                            deleted.add(self._coins[input])
                            del self._coins[input]

            for claimTx in [tx for tx in block.Transactions if tx.Type == TransactionType.ClaimTransaction]:

                for ref in claimTx.Claims:
                    if ref in self._coins.keys():
                        deleted.add(self._coins[ref])
                        del self._coins[ref]

            # update the current height of the wallet
            self._current_height += 1

            # in the case that another wallet implementation needs to do something
            # with the coins that have been changed ( ie persist to db ) this
            # method is called
            self.OnProcessNewBlock(block, added, changed, deleted)

            # this is not necessary at the moment, but any outside process
            # that wants to subscribe to the balance changed event could do
            # so from the BalanceChanged method
            if len(added) + len(deleted) + len(changed) > 0:
                self.BalanceChanged()

        except Exception as e:
            traceback.print_stack()
            traceback.print_exc()
            logger.error("could not process %s " % e)

    def Rebuild(self):
        """
        Sets the current height to 0 and now `ProcessBlocks` will start from
        the beginning of the blockchain.
        """
        self._coins = {}
        self._current_height = 0

    def OnProcessNewBlock(self, block, added, changed, deleted):
        # abstract
        pass

    def OnSaveTransaction(self, tx, added, changed, deleted):
        # abstract
        pass

    def BalanceChanged(self):
        # abstract
        pass

    def IsWalletTransaction(self, tx):
        """
        Verifies if a transaction belongs to the wallet.

        Args:
            tx (TransactionOutput):an instance of type neo.Core.TX.Transaction.TransactionOutput to verify.

        Returns:
            bool: True, if transaction belongs to wallet. False, if not.
        """
        for key, contract in self._contracts.items():

            for output in tx.outputs:
                if output.ScriptHash.ToBytes() == contract.ScriptHash.ToBytes():
                    return True

            for script in tx.scripts:

                if script.VerificationScript:
                    if bytes(contract.ScriptHash.Data) == script.VerificationScript:
                        return True

        for watch_script_hash in self._watch_only:
            for output in tx.outputs:
                if output.ScriptHash == watch_script_hash:
                    return True
            for script in tx.scripts:
                if script.VerificationScript == watch_script_hash.ToBytes():
                    return True

        return False

    def CheckAddressState(self, script_hash):
        """
        Determine the address state of the provided script hash.

        Args:
            script_hash (UInt160): a script hash to determine the address state of.

        Returns:
            AddressState: the address state.
        """
        for key, contract in self._contracts.items():
            if contract.ScriptHash.ToBytes() == script_hash.ToBytes():
                return AddressState.InWallet
        for watch in self._watch_only:
            if watch == script_hash:
                return AddressState.InWallet | AddressState.WatchOnly
        return AddressState.NoState

    @staticmethod
    def ToAddress(scripthash):
        """
        Transform a script hash to an address.

        Args:
            script_hash (UInt160): a bytearray (len 20) representing the public key.

        Returns:
            address (str): the base58check encoded address.
        """
        return scripthash_to_address(scripthash)

    def ToScriptHash(self, address):
        """
        Retrieve the script_hash based from an address.

        Args:
            address (str): a base58 encoded address.

        Raises:
            ValuesError: if an invalid address is supplied or the coin version is incorrect.
            Exception: if the address checksum fails.

        Returns:
            UInt160: script hash.
        """
        data = b58decode(address)
        if len(data) != 25:
            raise ValueError('Not correct Address, wrong length.')
        if data[0] != self.AddressVersion:
            raise ValueError('Not correct Coin Version')

        checksum = Crypto.Default().Hash256(data[:21])[:4]
        if checksum != data[21:]:
            raise Exception('Address format error')
        return UInt160(data=data[1:21])

    def ValidatePassword(self, password):
        """
        Validates if the provided password matches with the stored password.

        Args:
            password (string): a password.

        Returns:
            bool: the provided password matches with the stored password.
        """
        return hashlib.sha256(password.encode('utf-8')).digest() == self.LoadStoredData('PasswordHash')

    def GetStandardAddress(self):
        """
        Get the Wallet's default address.

        Raises:
            Exception: if no default contract address is set.

        Returns:
            UInt160: script hash.
        """
        for contract in self._contracts.values():
            if contract.IsStandard:
                return contract.ScriptHash

        raise Exception("Could not find a standard contract address")

    def GetChangeAddress(self, from_addr=None):
        """
        Get the address where change is send to.

        Args:
            from_address (UInt160): (optional) from address script hash.

        Raises:
            Exception: if change address could not be found.

        Returns:
            UInt160: script hash.
        """
        if from_addr is not None:
            for contract in self._contracts.values():
                if contract.ScriptHash == from_addr:
                    return contract.ScriptHash

        for contract in self._contracts.values():
            if contract.IsStandard:
                return contract.ScriptHash

        if len(self._contracts.values()):
            return self._contracts.values()[0]

        raise Exception("Could not find change address")

    def GetDefaultContract(self):
        """
        Get the default contract.

        Returns:
            contract (Contract): if Successful, a contract of type neo.SmartContract.Contract, otherwise an Exception.

        Raises:
            Exception: if no default contract is found.

        Note:
            Prints a warning to the console if the default contract could not be found.
        """
        try:
            return self.GetContracts()[0]
        except Exception as e:
            logger.error("Could not find default contract: %s" % str(e))
            raise

    def GetKeys(self):
        """
        Get all keys pairs present in the wallet.

        Returns:
            list: of KeyPairs.
        """
        return [key for key in self._keys.values()]

    def GetCoinAssets(self):
        """
        Get asset ids of all coins present in the wallet.

        Returns:
            list: of UInt256 asset id's.
        """
        assets = set()
        for coin in self.GetCoins():
            assets.add(coin.Output.AssetId)
        return list(assets)

    def GetCoins(self):
        """
        Get all coins in the wallet.

        Returns:
            list: a list of neo.Wallets.Coin objects.
        """
        return [coin for coin in self._coins.values()]

    def GetContract(self, script_hash):
        """
        Get contract for specified script_hash.

        Args:
            script_hash (UInt160): a bytearray (len 20).

        Returns:
            Contract: if a contract was found matching the provided script hash, otherwise None
        """
        if script_hash.ToBytes() in self._contracts.keys():
            return self._contracts[script_hash.ToBytes()]
        return None

    def GetContracts(self):
        """
        Get all contracts in the wallet.

        Returns:
            list: a list of neo.SmartContract.Contract objects.
        """
        return [contract for contract in self._contracts.values()]

    def MakeTransaction(self,
                        tx,
                        change_address=None,
                        fee=Fixed8(0),
                        from_addr=None,
                        use_standard=False,
                        watch_only_val=0,
                        exclude_vin=None,
                        use_vins_for_asset=None):
        """
        This method is used to to calculate the necessary TransactionInputs (CoinReferences) and TransactionOutputs to
        be used when creating a transaction that involves an exchange of system assets, ( NEO, Gas, etc ).

        Args:
            tx (Transaction): The Transaction to be used.
            change_address (UInt160): The address any change for the transaction should be returned to.
            fee (Fixed8): A fee to be attached to the Transaction for network processing purposes.
            from_addr (UInt160): If present, all CoinReferences selected will only come from this address.
            use_standard (bool): If true, only CoinReferences from standard addresses ( not contracts that are smart contracts ) will be used.
            watch_only_val (int): 0 or CoinState.WATCH_ONLY, if present only choose coins that are in a WatchOnly address.
            exclude_vin (list): A list of CoinReferences to NOT use in the making of this tx.
            use_vins_for_asset (list): A list of CoinReferences to use.

        Returns:
            tx: (Transaction) Returns the transaction with oupdated inputs and outputs.
        """

        tx.ResetReferences()
        tx.ResetHashData()

        if not tx.outputs:
            tx.outputs = []
        if not tx.inputs:
            tx.inputs = []

        fee = fee + (tx.SystemFee() * Fixed8.FD())

        #        pdb.set_trace()

        paytotal = {}
        if tx.Type != int.from_bytes(TransactionType.IssueTransaction, 'little'):

            for key, group in groupby(tx.outputs, lambda x: x.AssetId):
                sum = Fixed8(0)
                for item in group:
                    sum = sum + item.Value
                paytotal[key] = sum
        else:
            paytotal = {}

        if fee > Fixed8.Zero():

            if Blockchain.SystemCoin().Hash in paytotal.keys():
                paytotal[Blockchain.SystemCoin().Hash] = paytotal[Blockchain.SystemCoin().Hash] + fee
            else:
                paytotal[Blockchain.SystemCoin().Hash] = fee

        paycoins = {}

        self._vin_exclude = exclude_vin

        for assetId, amount in paytotal.items():

            if use_vins_for_asset is not None and len(use_vins_for_asset) > 0 and use_vins_for_asset[1] == assetId:
                paycoins[assetId] = self.FindCoinsByVins(use_vins_for_asset[0])
            else:
                paycoins[assetId] = self.FindUnspentCoinsByAssetAndTotal(
                    assetId, amount, from_addr=from_addr, use_standard=use_standard, watch_only_val=watch_only_val)

        self._vin_exclude = None

        for key, unspents in paycoins.items():
            if unspents is None:
                logger.error("insufficient funds for asset id: %s " % key)
                return None

        input_sums = {}

        for assetId, unspents in paycoins.items():
            sum = Fixed8(0)
            for coin in unspents:
                sum = sum + coin.Output.Value
            input_sums[assetId] = sum

        if not change_address:
            change_address = self.GetChangeAddress(from_addr=from_addr)

        new_outputs = []

        for assetId, sum in input_sums.items():
            if sum > paytotal[assetId]:
                difference = sum - paytotal[assetId]
                output = TransactionOutput(AssetId=assetId, Value=difference, script_hash=change_address)
                new_outputs.append(output)

        inputs = []

        for item in paycoins.values():
            for ref in item:
                inputs.append(ref.Reference)

        tx.inputs = inputs
        tx.outputs = tx.outputs + new_outputs

        return tx

    def SaveTransaction(self, tx):
        """
        This method is used to after a transaction has been made by this wallet.  It updates the states of the coins
        In the wallet to reflect the new balance, but the coins remain in a ``CoinState.UNCONFIRMED`` state until
        The transaction has been processed by the network.

        The results of these updates can be used by overriding the ``OnSaveTransaction`` method, and, for example
        persisting the results to a database.

        Args:
            tx (Transaction): The transaction that has been made by this wallet.

        Returns:
            bool: True is successfully processes, otherwise False if input is not in the coin list, already spent or not confirmed.
        """
        coins = self.GetCoins()
        changed = []
        added = []
        deleted = []
        found_coin = False
        for input in tx.inputs:
            coin = None

            for coinref in coins:
                test_coin = coinref.Reference
                if test_coin == input:
                    coin = coinref

            if coin is None:
                return False
            if coin.State & CoinState.Spent > 0:
                return False
            elif coin.State & CoinState.Confirmed == 0:
                return False

            coin.State |= CoinState.Spent
            coin.State &= ~CoinState.Confirmed
            changed.append(coin)

        for index, output in enumerate(tx.outputs):

            state = self.CheckAddressState(output.ScriptHash)

            key = CoinReference(tx.Hash, index)

            if state & AddressState.InWallet > 0:
                newcoin = Coin.CoinFromRef(coin_ref=key, tx_output=output, state=CoinState.Unconfirmed)
                self._coins[key] = newcoin

                if state & AddressState.WatchOnly > 0:
                    newcoin.State |= CoinState.WatchOnly

                added.append(newcoin)

        if isinstance(tx, ClaimTransaction):
            # do claim stuff
            for claim in tx.Claims:
                claim_coin = self._coins[claim]
                claim_coin.State |= CoinState.Claimed
                claim_coin.State &= ~CoinState.Confirmed
                changed.append(claim_coin)

        self.OnSaveTransaction(tx, added, changed, deleted)

        return True

    def Sign(self, context):
        """
        Sign the verifiable items ( Transaction, Block, etc ) in the context with the Keypairs in this wallet.

        Args:
            context (ContractParameterContext): the context to sign.

        Returns:
            bool: if signing is successful for all contracts in this wallet.
        """
        success = False

        for hash in context.ScriptHashes:

            contract = self.GetContract(hash)
            if contract is None:
                continue

            key = self.GetKeyByScriptHash(hash)

            if key is None:
                continue

            signature = Helper.Sign(context.Verifiable, key)

            res = context.AddSignature(contract, key.PublicKey, signature)

            success |= res

        return success

    def GetSyncedBalances(self):
        """
        Returns a list of synced balances. The list looks like this:
        [('NEO', 100.0), ('NEOGas', 100.0)]

        Returns
            list: [(asset_name, amount), ...]
        """
        assets = self.GetCoinAssets()
        balances = []
        for asset in assets:
            if type(asset) is UInt256:
                bc_asset = Blockchain.Default().GetAssetState(asset.ToBytes())
                total = self.GetBalance(asset).value / Fixed8.D
                balances.append((bc_asset.GetName(), total))
            elif type(asset) is NEP5Token:
                balances.append((asset.symbol, self.GetBalance(asset)))
        return balances

    def ToJson(self, verbose=False):
        # abstract
        pass
