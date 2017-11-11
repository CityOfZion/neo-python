from neo.Settings import settings as rpc_settings
from neo.Core.Block import Block
from neo.Core.TX.Transaction import Transaction
import requests
import binascii


class RPCClient():

    id_counter = 0

    _settings = rpc_settings
    _addr_list = None

    @property
    def endpoints(self):
        return self._addr_list

    @property
    def default_enpoint(self):
        self._addr_list.sort()
        return self._addr_list[0]

    def get_account(self, address, id=None, endpoint=None):
        """
        Look up an account on the blockchain.  Sample output:

        Args:
            address: (str) address to lookup ( in format 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK')
            id: (int, optional) id to use for response tracking
            endpoint: (RPCEndpoint, optional) endpoint to specify to use

        Returns:
            json object of the result or the error encountered in the RPC call

        """
        return self._call_endpoint(GET_ACCOUNT_STATE, params=[address], id=id, endpoint=endpoint)

    def get_height(self, id=None, endpoint=None):
        """
        Get the current height of the blockchain
        Args:
            id: (int, optional) id to use for response tracking
            endpoint: (RPCEndpoint, optional) endpoint to specify to use

        Returns:
            json object of the result or the error encountered in the RPC call
        """
        return self._call_endpoint(GET_BLOCK_COUNT, id=id, endpoint=endpoint)

    def get_asset(self, asset_hash, id=None, endpoint=None):
        """
        Get an asset by its hash
        Args:
            asset_hash: (str) asset to lookup, example would be 'c56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b'
            id: (int, optional) id to use for response tracking
            endpoint: (RPCEndpoint, optional) endpoint to specify to use

        Returns:
            json object of the result or the error encountered in the RPC call
        """
        return self._call_endpoint(GET_ASSET_STATE, params=[asset_hash], id=id, endpoint=endpoint)

    def get_best_blockhash(self, id=None, endpoint=None):
        """
        Get the hash of the highest block
        Args:
            id: (int, optional) id to use for response tracking
            endpoint: (RPCEndpoint, optional) endpoint to specify to use
        Returns:
            json object of the result or the error encountered in the RPC call
        """
        return self._call_endpoint(GET_BEST_BLOCK_HASH, id=id, endpoint=endpoint)

    def get_block(self, height_or_hash, as_json=True, id=None, endpoint=None):
        """
        Look up a block by the height or hash of the block. Optionally parse result as ``neo.Core.Block.Block`` object and return result.
        Args:
            height_or_hash: (int or str) either the height of the desired block or its hash in the form '1e67372c158a4cfbb17b9ad3aaae77001a4247a00318e354c62e53b56af4006f'
            as_json: whether to return a json object of the block or a ``neo.Core.Block.Block`` object
            id: (int, optional) id to use for response tracking
            endpoint: (RPCEndpoint, optional) endpoint to specify to use

        Returns:
            block: either the block as a json object or the ``neo.Core.Block.Block`` object
        """
        if as_json:
            return self._call_endpoint(GET_BLOCK, params=[height_or_hash, 1], id=id, endpoint=endpoint)

        result = self._call_endpoint(GET_BLOCK, params=[height_or_hash, 0], id=id, endpoint=endpoint)

        return Block.FromTrimmedData(binascii.unhexlify(result))

    def get_block_hash(self, height, id=None, endpoint=None):
        """
        Get hash of a block by its height
        Args:
            height: (int) height of the block to lookup
            id: (int, optional) id to use for response tracking
            endpoint: (RPCEndpoint, optional) endpoint to specify to use

        Returns:
            json object of the result or the error encountered in the RPC call
        """
        return self._call_endpoint(GET_BLOCK_HASH, params=[height], id=id, endpoint=endpoint)

    def get_block_sysfee(self, height, id=None, endpoint=None):
        """
        Get the system fee of a block by height.  This is used in calculating gas claims
        Args:
            height: (int) height of the block to lookup
            id: (int, optional) id to use for response tracking
            endpoint: (RPCEndpoint, optional) endpoint to specify to use

        Returns:
            json object of the result or the error encountered in the RPC call
        """
        return self._call_endpoint(GET_BLOCK_SYS_FEE, params=[height], id=id, endpoint=endpoint)

    def get_connection_count(self, id=None, endpoint=None):
        """
        Gets the number of nodes connected to the endpoint
        Args:
            id: (int, optional) id to use for response tracking
            endpoint: (RPCEndpoint, optional) endpoint to specify to use
        Returns:
            json object of the result or the error encountered in the RPC call
        """
        return self._call_endpoint(GET_CONNECTION_COUNT, params=[], id=id, endpoint=endpoint)

    def get_contract_state(self, contract_hash, id=None, endpoint=None):
        """
        Get a contract state object by its hash
        Args:
            contract_hash: (str) the hash of the contract to lookup, for example 'd7678dd97c000be3f33e9362e673101bac4ca654'
            id: (int, optional) id to use for response tracking
            endpoint: (RPCEndpoint, optional) endpoint to specify to use
        Returns:
            json object of the result or the error encountered in the RPC call
        """
        return self._call_endpoint(GET_CONTRACT_STATE, params=[contract_hash], id=id, endpoint=endpoint)

    def get_raw_mempool(self, id=None, endpoint=None):
        """
        Returns the tx that are in the memorypool of the endpoint
        Args:
            id: (int, optional) id to use for response tracking
            endpoint: (RPCEndpoint, optional) endpoint to specify to use
        Returns:
            json object of the result or the error encountered in the RPC call
        """
        return self._call_endpoint(GET_RAW_MEMPOOL, params=[], id=id, endpoint=endpoint)

    def get_transaction(self, tx_hash, as_json=True, id=None, endpoint=None):
        """
        Look up a transaction by hash. Optionally parse result as ``neo.Core.TX.Transaction.Transaction`` object and return result.
        Args:
            tx_hash: (str) hash in the form '58c634f81fbd4ae2733d7e3930a9849021840fc19dc6af064d6f2812a333f91d'
            as_json: whether to return a json object of the transaction or a `neo.Core.TX.Transaction.Transaction`` object
            id: (int, optional) id to use for response tracking
            endpoint: (RPCEndpoint, optional) endpoint to specify to use

        Returns:
            block: either the transaction as a json object or the `neo.Core.TX.Transaction.Transaction`` object
        """
        if as_json:
            return self._call_endpoint(GET_RAW_TRANSACTION, params=[tx_hash, 1], id=id, endpoint=endpoint)

        result = self._call_endpoint(GET_RAW_TRANSACTION, params=[tx_hash, 0], id=id, endpoint=endpoint)

        return Transaction.DeserializeFromBufer(binascii.unhexlify(result), 0)

    def get_storage(self, contract_hash, storage_key, id=None, endpoint=None):
        """
        Returns a storage item of a specified contract
        Args:
            contract_hash: (str) hash of the contract to lookup, for example 'd7678dd97c000be3f33e9362e673101bac4ca654'
            storage_key: (str) storage key to lookup, for example 'totalSupply'
            id: (int, optional) id to use for response tracking
            endpoint: (RPCEndpoint, optional) endpoint to specify to use
        Returns:
            bytearray: bytearray value of the storage item
        """
        result = self._call_endpoint(GET_STORAGE, params=[contract_hash, binascii.hexlify(storage_key.encode('utf-8')).decode('utf-8')], id=id, endpoint=endpoint)
        try:

            return bytearray(binascii.unhexlify(result.encode('utf-8')))
        except Exception as e:
            print("could not decode result %s " % e)
        return None

    def get_tx_out(self, tx_hash, vout_id, id=None, endpoint=None):
        """
        Gets a transaction output by specified transaction hash and output index
        Args:
            tx_hash: (str) hash in the form '58c634f81fbd4ae2733d7e3930a9849021840fc19dc6af064d6f2812a333f91d'
            vout_id: (int) index of the transaction output in the transaction
            id: (int, optional) id to use for response tracking
            endpoint: (RPCEndpoint, optional) endpoint to specify to use
        Returns:
            json object of the result or the error encountered in the RPC call
        """
        return self._call_endpoint(GET_TX_OUT, params=[tx_hash, vout_id], id=id, endpoint=endpoint)

    def invoke_contract(self, contract_hash, params, id=None, endpoint=None):
        """
        Invokes a contract
        Args:
            contract_hash: (str) hash of the contract, for example 'd7678dd97c000be3f33e9362e673101bac4ca654'
            params: (list) a list of json ContractParameters to pass along with the invocation, example [{'type':7,'value':'symbol'},{'type':16, 'value':[]}]
            id: (int, optional) id to use for response tracking
            endpoint: (RPCEndpoint, optional) endpoint to specify to use
        Returns:
            json object of the result or the error encountered in the RPC call
        """
        return self._call_endpoint(INVOKE, params=[contract_hash, params], id=id, endpoint=endpoint)

    def invoke_contract_fn(self, contract_hash, operation, params=None, id=None, endpoint=None):
        """
        Invokes a contract
        Args:
            contract_hash: (str) hash of the contract, for example 'd7678dd97c000be3f33e9362e673101bac4ca654'
            operation: (str) the operation to call on the contract
            params: (list) a list of json ContractParameters to pass along with the invocation, example [{'type':7,'value':'symbol'},{'type':16, 'value':[]}]
            id: (int, optional) id to use for response tracking
            endpoint: (RPCEndpoint, optional) endpoint to specify to use
        Returns:
            json object of the result or the error encountered in the RPC call
        """
        return self._call_endpoint(INVOKE_FUNCTION, params=[contract_hash, operation, params if params else []], id=id, endpoint=endpoint)

    def invoke_script(self, script, id=None, endpoint=None):
        """
        Invokes a script that has been assembled
        Args:
            script: (str) a hexlified string of a contract invocation script, example '00c10b746f74616c537570706c796754a64cac1b1073e662933ef3e30b007cd98d67d7'
            id: (int, optional) id to use for response tracking
            endpoint: (RPCEndpoint, optional) endpoint to specify to use
        Returns:
            json object of the result or the error encountered in the RPC call
        """
        return self._call_endpoint(INVOKE_SCRIPT, params=[script], id=id, endpoint=endpoint)

    def send_raw_tx(self, serialized_tx, id=None, endpoint=None):
        """
        Submits a serialized tx to the network
        Args:
            serialized_tx: (str) a hexlified string of a transaction
            id: (int, optional) id to use for response tracking
            endpoint: (RPCEndpoint, optional) endpoint to specify to use
        Returns:
            bool: whether the tx was accepted or not
        """
        return self._call_endpoint(SEND_TX, params=[serialized_tx], id=id, endpoint=endpoint)

    def validate_addr(self, address, id=None, endpoint=None):
        """
        returns whether or not addr string is valid

        Args:
            address: (str) address to lookup ( in format 'AXjaFSP23Jkbe6Pk9pPGT6NBDs1HVdqaXK')
            id: (int, optional) id to use for response tracking
            endpoint: (RPCEndpoint, optional) endpoint to specify to use

        Returns:
            json object of the result or the error encountered in the RPC call

        """
        return self._call_endpoint(VALIDATE_ADDR, params=[address], id=id, endpoint=endpoint)

    def get_peers(self, id=None, endpoint=None):
        """
        Get the current peers of a remote node
        Args:
            id: (int, optional) id to use for response tracking
            endpoint: (RPCEndpoint, optional) endpoint to specify to use

        Returns:
            json object of the result or the error encountered in the RPC call
        """
        return self._call_endpoint(GET_PEERS, id=id, endpoint=endpoint)

# Not all endpoints currently implement this method
#    def get_version(self, id=None, endpoint=None):
#        """
#        Get the current version of the endpoint
#        Args:
#            id: (int, optional) id to use for response tracking
#            endpoint: (RPCEndpoint, optional) endpoint to specify to use
#        Returns:
#            json object of the result or the error encountered in the RPC call
#        """
#        return self._call_endpoint(GET_VERSION, id=id, endpoint=endpoint)

    def __init__(self, config=None, setup=False):

        if config:
            self._settings = config

        self._build_addr()

        if setup:
            self.setup_endpoints()

    def setup_endpoints(self):
        self._build_addr()
        [endpoint.setup() for endpoint in self._addr_list]

    def _call_endpoint(self, method, params=None, id=None, endpoint=None):
        payload = self._build_payload(method, params, id)
        endpoint = self.default_enpoint if endpoint is None else endpoint
        try:
            response = requests.post(endpoint.addr, json=payload, timeout=TIMEOUT)
            response.raise_for_status()
            if response.status_code == 200:
                if 'result' in response.json():
                    return response.json()['result']
            return response.json()
        except Exception as e:
            print("Could not call method %s with endpoint: %s : %s " % (method, endpoint.addr, e))
        return None

    def _build_addr(self):
        self._addr_list = [RPCEnpoint(self, addr) for addr in self._settings.RPC_LIST]

    def _build_payload(self, method, params, id):

        id = self.id_counter if id is None else id
        self.id_counter += 1

        params = [] if params is None else params

        rpc_version = "2.0"

        return {'jsonrpc': rpc_version, 'method': method, 'params': params, 'id': id}


# methods that read data
GET_ACCOUNT_STATE = 'getaccountstate'
GET_ASSET_STATE = 'getassetstate'
GET_BEST_BLOCK_HASH = 'getbestblockhash'
GET_BLOCK = 'getblock'
GET_BLOCK_COUNT = 'getblockcount'
GET_BLOCK_HASH = 'getblockhash'
GET_BLOCK_SYS_FEE = 'getblocksysfee'
GET_CONNECTION_COUNT = 'getconnectioncount'
GET_CONTRACT_STATE = 'getcontractstate'
GET_RAW_MEMPOOL = 'getrawmempool'
GET_RAW_TRANSACTION = 'getrawtransaction'
GET_STORAGE = 'getstorage'
GET_TX_OUT = 'gettxout'
GET_PEERS = 'getpeers'
GET_VERSION = 'getversion'

# invocation related methods
INVOKE = 'invoke'
INVOKE_FUNCTION = 'invokefunction'
INVOKE_SCRIPT = 'invokescript'

# send
SEND_TX = 'sendrawtransaction'
SUBMIT_BLOCK = 'submitblock'

# validate
VALIDATE_ADDR = 'validateaddress'


TIMEOUT = 10


class RPCEnpoint():
    addr = None
    height = None
    client = None
    status = None
    elapsed = None

    def __init__(self, client, address):
        self.client = client
        self.addr = address

    def setup(self):

        response = requests.post(self.addr, json={'jsonrpc': '2.0', 'method': GET_BLOCK_COUNT, 'params': [], 'id': 1})
        self.update_enpoint_details(response)

        if response.status_code == 200:
            json = response.json()
            self.height = int(json['result'])

    def update_enpoint_details(self, response):

        self.status = response.status_code
        self.elapsed = response.elapsed.microseconds

    def _compare(self, other):
        if self.status != 200:
            return -1
        elif other.status != 200:
            return 1

        if self.height == other.height:
            if other.elapsed > 0 and self.elapsed > 0:
                if self.elapsed > other.elapsed:
                    return 1
                else:
                    return -1
        else:

            if self.height < other.height:
                return 1
            else:
                return -1

        return 0

    def __eq__(self, other):
        return self.addr == other.addr

    def __lt__(self, other):
        return self._compare(other) < 0

    def __gt__(self, other):
        return self._compare(other) > 0

    def __le__(self, other):
        return self._compare(other) <= 0

    def __ge__(self, other):
        return self._compare(other) >= 0

    def __str__(self):
        return "[%s] %s %s %s  " % (self.addr, self.status, self.height, self.elapsed)
