"""
The JSON-RPC API is using the Python package 'klein', which makes it possible to
create HTTP routes and handlers with Twisted in a similar style to Flask:
https://github.com/twisted/klein

See also:
* http://www.jsonrpc.org/specification
"""
import json
import base58
import binascii
from json.decoder import JSONDecodeError

from klein import Klein

from neo.Settings import settings
from neo.Core.Blockchain import Blockchain
from neo.api.utils import json_response, cors_header
from neo.Core.State.AccountState import AccountState
from neo.Core.TX.Transaction import Transaction, TransactionOutput, \
    ContractTransaction, TXFeeError
from neo.Core.TX.TransactionAttribute import TransactionAttribute, \
    TransactionAttributeUsage
from neo.Core.State.CoinState import CoinState
from neocore.UInt160 import UInt160
from neocore.UInt256 import UInt256
from neocore.Fixed8 import Fixed8
from neo.Core.Helper import Helper
from neo.Network.NodeLeader import NodeLeader
from neo.Core.State.StorageKey import StorageKey
from neo.SmartContract.ApplicationEngine import ApplicationEngine
from neo.SmartContract.ContractParameter import ContractParameter
from neo.SmartContract.ContractParameterContext import ContractParametersContext
from neo.VM.ScriptBuilder import ScriptBuilder
from neo.VM.VMState import VMStateStr
from neo.Implementations.Wallets.peewee.Models import Account
from neo.Prompt.Utils import get_asset_id
from neo.Wallets.Wallet import Wallet
from furl import furl
import ast


class JsonRpcError(Exception):
    """
    Easy error handling throughout the handlers. Allows for easy code overrides
    to be compliant with neo-cli responses
    """
    # standard json-rpc errors as per spec: http://www.jsonrpc.org/specification
    # PARSE_ERROR = {"code": -32700, "message": "Parse error"}
    # INVALID_REQUEST = {"code": -32600, "message": "Invalid Request"}
    # METHOD_NOT_FOUND = {"code": -32601, "message": "Method not found"}
    # INVALID_PARAMS = {"code": -32602, "message": "Invalid params"}
    # INTERNAL_ERROR = {"code": -32603, "message": "Internal error"}
    # SERVER_ERROR = {"code": -32000, "message": "Server error"}

    message = None
    code = None

    def __init__(self, code, message):
        super(JsonRpcError, self).__init__(message)
        self.code = code
        self.message = message

    @staticmethod
    def parseError(message=None):
        return JsonRpcError(-32700, message or "Parse error")

    @staticmethod
    def methodNotFound(message=None):
        return JsonRpcError(-32601, message or "Method not found")

    @staticmethod
    def invalidRequest(message=None):
        return JsonRpcError(-32600, message or "Invalid Request")

    @staticmethod
    def internalError(message=None):
        return JsonRpcError(-32603, message or "Internal error")


class JsonRpcApi:
    app = Klein()
    port = None

    def __init__(self, port, wallet=None):
        self.port = port
        self.wallet = wallet

    def get_data(self, body: dict):

        try:
            request_id = body["id"] if body and "id" in body else None

            if "jsonrpc" not in body or body["jsonrpc"] != "2.0":
                raise JsonRpcError.invalidRequest("Invalid value for 'jsonrpc'")

            if "id" not in body:
                raise JsonRpcError.invalidRequest("Field 'id' is missing")

            if "method" not in body:
                raise JsonRpcError.invalidRequest("Field 'method' is missing")

            params = body["params"] if "params" in body else None
            result = self.json_rpc_method_handler(body["method"], params)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }

        except JsonRpcError as e:
            return self.get_custom_error_payload(request_id, e.code, e.message)

        except Exception as e:
            error = JsonRpcError.internalError(str(e))
            return self.get_custom_error_payload(request_id, error.code, error.message)

    #
    # JSON-RPC API Route
    #
    @app.route('/')
    @json_response
    @cors_header
    def home(self, request):
        # POST Examples:
        # {"jsonrpc": "2.0", "id": 5, "method": "getblockcount", "params": []}
        # or multiple requests in 1 transaction
        # [{"jsonrpc": "2.0", "id": 1, "method": "getblock", "params": [10]}, {"jsonrpc": "2.0", "id": 2, "method": "getblock", "params": [10,1]}]
        #
        # GET Example:
        # /?jsonrpc=2.0&id=5&method=getblockcount&params=[]
        # NOTE: GET requests do not support multiple requests in 1 transaction
        request_id = None

        if "POST" == request.method.decode("utf-8"):
            try:
                content = json.loads(request.content.read().decode("utf-8"))

                # test if it's a multi-request message
                if isinstance(content, list):
                    result = []
                    for body in content:
                        result.append(self.get_data(body))
                    return result

                # otherwise it's a single request
                return self.get_data(content)

            except JSONDecodeError as e:
                error = JsonRpcError.parseError()
                return self.get_custom_error_payload(request_id, error.code, error.message)

        elif "GET" == request.method.decode("utf-8"):
            content = furl(request.uri).args

            # remove hanging ' or " from last value if value is not None to avoid SyntaxError
            try:
                l_value = list(content.values())[-1]
            except IndexError:
                error = JsonRpcError.parseError()
                return self.get_custom_error_payload(request_id, error.code, error.message)

            if l_value is not None:
                n_value = l_value[:-1]
                l_key = list(content.keys())[-1]
                content[l_key] = n_value

            if len(content.keys()) > 3:
                try:
                    params = content['params']
                    l_params = ast.literal_eval(params)
                    content['params'] = [l_params]
                except KeyError:
                    error = JsonRpcError(-32602, "Invalid params")
                    return self.get_custom_error_payload(request_id, error.code, error.message)

            return self.get_data(content)

        elif "OPTIONS" == request.method.decode("utf-8"):
            return self.options_response()

        error = JsonRpcError.invalidRequest("%s is not a supported HTTP method" % request.method.decode("utf-8"))
        return self.get_custom_error_payload(request_id, error.code, error.message)

    @classmethod
    def options_response(cls):
        # new plugins should update this response
        return {'supported HTTP methods': ("GET", "POST"),
                'JSON-RPC server type': "default"}

    def json_rpc_method_handler(self, method, params):

        if method == "getaccountstate":
            acct = Blockchain.Default().GetAccountState(params[0])
            if acct is None:
                try:
                    acct = AccountState(script_hash=Helper.AddrStrToScriptHash(params[0]))
                except Exception as e:
                    raise JsonRpcError(-2146233033, "One of the identified items was in an invalid format.")

            return acct.ToJson()

        elif method == "getassetstate":
            asset_str = params[0]
            if asset_str.lower() == 'neo':
                assetId = Blockchain.Default().SystemShare().Hash
            elif asset_str.lower() == 'gas':
                assetId = Blockchain.Default().SystemCoin().Hash
            else:
                assetId = UInt256.ParseString(params[0])
            asset = Blockchain.Default().GetAssetState(assetId.ToBytes())
            if asset:
                return asset.ToJson()
            raise JsonRpcError(-100, "Unknown asset")

        elif method == "getbestblockhash":
            return '0x%s' % Blockchain.Default().CurrentHeaderHash.decode('utf-8')

        elif method == "getblock":
            # this should work for either str or int
            block = Blockchain.Default().GetBlock(params[0])
            if not block:
                raise JsonRpcError(-100, "Unknown block")
            return self.get_block_output(block, params)

        elif method == "getblockcount":
            return Blockchain.Default().Height + 1

        elif method == "getblockhash":
            height = params[0]
            if height >= 0 and height <= Blockchain.Default().Height:
                return '0x%s' % Blockchain.Default().GetBlockHash(height).decode('utf-8')
            else:
                raise JsonRpcError(-100, "Invalid Height")

        elif method == "getblocksysfee":
            height = params[0]
            if height >= 0 and height <= Blockchain.Default().Height:
                return Blockchain.Default().GetSysFeeAmountByHeight(height)
            else:
                raise JsonRpcError(-100, "Invalid Height")

        elif method == "getconnectioncount":
            return len(NodeLeader.Instance().Peers)

        elif method == "getcontractstate":
            script_hash = UInt160.ParseString(params[0])
            contract = Blockchain.Default().GetContract(script_hash.ToBytes())
            if contract is None:
                raise JsonRpcError(-100, "Unknown contract")
            return contract.ToJson()

        elif method == "getrawmempool":
            return list(map(lambda hash: "0x%s" % hash.decode('utf-8'), NodeLeader.Instance().MemPool.keys()))

        elif method == "getversion":
            return {
                "port": self.port,
                "nonce": NodeLeader.Instance().NodeId,
                "useragent": settings.VERSION_NAME
            }

        elif method == "getrawtransaction":
            tx_id = UInt256.ParseString(params[0])
            tx, height = Blockchain.Default().GetTransaction(tx_id)
            if not tx:
                raise JsonRpcError(-100, "Unknown Transaction")
            return self.get_tx_output(tx, height, params)

        elif method == "getstorage":
            script_hash = UInt160.ParseString(params[0])
            key = binascii.unhexlify(params[1].encode('utf-8'))
            storage_key = StorageKey(script_hash=script_hash, key=key)
            storage_item = Blockchain.Default().GetStorageItem(storage_key)
            if storage_item:
                return storage_item.Value.hex()
            return None

        elif method == "gettransactionheight":
            try:
                hash = UInt256.ParseString(params[0])
            except Exception:
                # throws exception, not anything more specific
                raise JsonRpcError(-100, "Unknown transaction")

            tx, height = Blockchain.Default().GetTransaction(hash)
            if tx:
                return height
            else:
                raise JsonRpcError(-100, "Unknown transaction")

        elif method == "gettxout":
            hash = params[0].encode('utf-8')
            index = params[1]
            utxo = Blockchain.Default().GetUnspent(hash, index)
            if utxo:
                return utxo.ToJson(index)
            else:
                return None

        elif method == "invoke":
            shash = UInt160.ParseString(params[0])
            contract_parameters = [ContractParameter.FromJson(p) for p in params[1]]
            sb = ScriptBuilder()
            sb.EmitAppCallWithJsonArgs(shash, contract_parameters)
            return self.get_invoke_result(sb.ToArray())

        elif method == "invokefunction":
            contract_parameters = []
            if len(params) > 2:
                contract_parameters = [ContractParameter.FromJson(p).ToVM() for p in params[2]]
            sb = ScriptBuilder()
            sb.EmitAppCallWithOperationAndArgs(UInt160.ParseString(params[0]), params[1], contract_parameters)
            return self.get_invoke_result(sb.ToArray())

        elif method == "invokescript":
            script = params[0].encode('utf-8')
            return self.get_invoke_result(script)

        elif method == "sendrawtransaction":
            tx_script = binascii.unhexlify(params[0].encode('utf-8'))
            transaction = Transaction.DeserializeFromBufer(tx_script)
            result = NodeLeader.Instance().Relay(transaction)
            return result

        elif method == "validateaddress":
            return self.validateaddress(params)

        elif method == "getpeers":
            return self.get_peers()

        elif method == "getbalance":
            if self.wallet:
                return self.get_balance(params)
            else:
                raise JsonRpcError(-400, "Access denied.")

        elif method == "getwalletheight":
            if self.wallet:
                return self.wallet.WalletHeight
            else:
                raise JsonRpcError(-400, "Access denied.")

        elif method == "listaddress":
            if self.wallet:
                return self.list_address()
            else:
                raise JsonRpcError(-400, "Access denied.")

        elif method == "getnewaddress":
            if self.wallet:
                keys = self.wallet.CreateKey()
                account = Account.get(
                    PublicKeyHash=keys.PublicKeyHash.ToBytes()
                )
                return account.contract_set[0].Address.ToString()
            else:
                raise JsonRpcError(-400, "Access denied.")

        elif method == "sendtoaddress":
            if self.wallet:
                contract_tx, fee = self.parse_send_to_address_params(params)
                return self.process_transaction(contract_tx=contract_tx, fee=fee)
            else:
                raise JsonRpcError(-400, "Access denied.")

        elif method == "sendfrom":
            if self.wallet:
                contract_tx, address_from, fee, change_addr = self.parse_send_from_params(params)
                return self.process_transaction(contract_tx=contract_tx, fee=fee, address_from=address_from, change_addr=change_addr)
            else:
                raise JsonRpcError(-400, "Access denied.")

        elif method == "sendmany":
            if self.wallet:
                contract_tx, fee, change_addr = self.parse_send_many_params(params)
                return self.process_transaction(contract_tx=contract_tx, fee=fee, change_addr=change_addr)
            else:
                raise JsonRpcError(-400, "Access denied.")

        elif method == "getblockheader":
            # this should work for either str or int
            blockheader = Blockchain.Default().GetHeaderBy(params[0])
            if not blockheader:
                raise JsonRpcError(-100, "Unknown block")
            return self.get_blockheader_output(blockheader, params)

        raise JsonRpcError.methodNotFound()

    def get_custom_error_payload(self, request_id, code, message):
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }

    def get_tx_output(self, tx, height, params):

        if len(params) >= 2 and params[1]:
            jsn = tx.ToJson()
            if height >= 0:
                header = Blockchain.Default().GetHeaderByHeight(height)
                jsn['blockhash'] = header.Hash.To0xString()
                jsn['confirmations'] = Blockchain.Default().Height - header.Index + 1
                jsn['blocktime'] = header.Timestamp
            return jsn

        return Helper.ToArray(tx).decode('utf-8')

    def get_block_output(self, block, params):

        block.LoadTransactions()

        if len(params) >= 2 and params[1]:
            jsn = block.ToJson()
            jsn['confirmations'] = Blockchain.Default().Height - block.Index + 1
            hash = Blockchain.Default().GetNextBlockHash(block.Hash)
            if hash:
                jsn['nextblockhash'] = '0x%s' % hash.decode('utf-8')
            return jsn

        return Helper.ToArray(block).decode('utf-8')

    def get_invoke_result(self, script):

        appengine = ApplicationEngine.Run(script=script)
        return {
            "script": script.decode('utf-8'),
            "state": VMStateStr(appengine.State),
            "gas_consumed": appengine.GasConsumed().ToString(),
            "stack": [ContractParameter.ToParameter(item).ToJson() for item in appengine.ResultStack.Items]
        }

    def validateaddress(self, params):
        # check for [] parameter or [""]
        if not params or params[0] == '':
            raise JsonRpcError(-100, "Missing argument")

        isValid = False
        try:
            data = base58.b58decode_check(params[0])
            if len(data) == 21 and data[0] == settings.ADDRESS_VERSION:
                isValid = True
        except Exception as e:
            pass

        return {"address": params[0], "isvalid": isValid}

    def get_peers(self):
        """Get all known nodes and their 'state' """
        node = NodeLeader.Instance()
        result = {"connected": [], "unconnected": [], "bad": []}
        connected_peers = []

        for peer in node.Peers:
            result['connected'].append({"address": peer.host,
                                        "port": peer.port})
            connected_peers.append("{}:{}".format(peer.host, peer.port))

        for addr in node.DEAD_ADDRS:
            host, port = addr.rsplit(':', 1)
            result['bad'].append({"address": host, "port": port})

        # "UnconnectedPeers" is never used. So a check is needed to
        # verify that a given address:port does not belong to a connected peer
        for addr in node.KNOWN_ADDRS:
            host, port = addr.rsplit(':', 1)
            if addr not in connected_peers:
                result['unconnected'].append({"address": host,
                                              "port": int(port)})

        return result

    def get_balance(self, params):
        if len(params) != 1:
            raise JsonRpcError(-400, "Params should contain 1 id.")

        asset_id = get_asset_id(self.wallet, params[0])
        result = {}

        if type(asset_id) is UInt256:
            total = Fixed8(0)
            for c in self.wallet.GetCoins():
                if c.Output.AssetId == asset_id and c.State & CoinState.WatchOnly == 0:
                    total += c.Output.Value

            result['Balance'] = str(total)
            result["Confirmed"] = str(self.wallet.GetBalance(asset_id).value / Fixed8.D)
        else:
            result["Balance"] = str(self.wallet.GetBalance(asset_id))

        return result

    def list_address(self):
        """Get information about all the addresses present on the open wallet"""
        result = []
        for addrStr in self.wallet.Addresses:
            addr = self.wallet.GetAddress(addrStr)
            result.append({
                "address": addrStr,
                "haskey": not addr.IsWatchOnly,
                "label": None,
                "watchonly": addr.IsWatchOnly,
            })
        return result

    def parse_send_to_address_params(self, params):
        if len(params) not in [3, 4]:
            raise JsonRpcError(-32602, "Invalid params")

        asset_id = get_asset_id(self.wallet, params[0])
        if not type(asset_id) is UInt256:
            raise JsonRpcError(-32602, "Invalid params")

        address_to = params[1]
        try:
            address_to_sh = self.wallet.ToScriptHash(address_to)
        except Exception:
            raise JsonRpcError(-32602, "Invalid params")

        amount = Fixed8.TryParse(params[2], require_positive=True)
        if not amount or float(params[2]) == 0:
            raise JsonRpcError(-32602, "Invalid params")

        output = TransactionOutput(AssetId=asset_id,
                                   Value=amount,
                                   script_hash=address_to_sh)
        contract_tx = ContractTransaction(outputs=[output])

        fee = Fixed8.TryParse(params[3]) if len(params) == 4 else Fixed8.Zero()
        if fee < Fixed8.Zero():
            raise JsonRpcError(-32602, "Invalid params")

        return contract_tx, fee

    def parse_send_from_params(self, params):
        if len(params) not in [4, 5, 6]:
            raise JsonRpcError(-32602, "Invalid params")
        asset_id = get_asset_id(self.wallet, params[0])
        if not type(asset_id) is UInt256:
            raise JsonRpcError(-32602, "Invalid params")
        address_from = params[1]
        try:
            address_from_sh = self.wallet.ToScriptHash(address_from)
        except Exception:
            raise JsonRpcError(-32602, "Invalid params")
        address_to = params[2]
        try:
            address_to_sh = self.wallet.ToScriptHash(address_to)
        except Exception:
            raise JsonRpcError(-32602, "Invalid params")
        amount = Fixed8.TryParse(params[3], require_positive=True)
        if not amount or float(params[3]) == 0:
            raise JsonRpcError(-32602, "Invalid params")
        output = TransactionOutput(AssetId=asset_id,
                                   Value=amount,
                                   script_hash=address_to_sh)
        contract_tx = ContractTransaction(outputs=[output])
        fee = Fixed8.TryParse(params[4]) if len(params) >= 5 else Fixed8.Zero()
        if fee < Fixed8.Zero():
            raise JsonRpcError(-32602, "Invalid params")
        change_addr_sh = None
        if len(params) >= 6:
            change_addr = params[5]
            try:
                change_addr_sh = self.wallet.ToScriptHash(change_addr)
            except Exception:
                raise JsonRpcError(-32602, "Invalid params")
        return contract_tx, address_from_sh, fee, change_addr_sh

    def parse_send_many_params(self, params):
        if type(params[0]) is not list:
            raise JsonRpcError(-32602, "Invalid params")
        if len(params) not in [1, 2, 3]:
            raise JsonRpcError(-32602, "Invalid params")
        output = []
        for info in params[0]:
            asset = get_asset_id(self.wallet, info['asset'])
            if not type(asset) is UInt256:
                raise JsonRpcError(-32602, "Invalid params")
            address = info["address"]
            try:
                address = self.wallet.ToScriptHash(address)
            except Exception:
                raise JsonRpcError(-32602, "Invalid params")
            amount = Fixed8.TryParse(info["value"], require_positive=True)
            if not amount or float(info["value"]) == 0:
                raise JsonRpcError(-32602, "Invalid params")
            tx_output = TransactionOutput(AssetId=asset,
                                          Value=amount,
                                          script_hash=address)
            output.append(tx_output)
        contract_tx = ContractTransaction(outputs=output)
        fee = Fixed8.TryParse(params[1]) if len(params) >= 2 else Fixed8.Zero()
        if fee < Fixed8.Zero():
            raise JsonRpcError(-32602, "Invalid params")
        change_addr_sh = None
        if len(params) >= 3:
            change_addr = params[2]
            try:
                change_addr_sh = self.wallet.ToScriptHash(change_addr)
            except Exception:
                raise JsonRpcError(-32602, "Invalid params")
        return contract_tx, fee, change_addr_sh

    def process_transaction(self, contract_tx, fee=None, address_from=None, change_addr=None):
        standard_contract = self.wallet.GetStandardAddress()
        signer_contract = self.wallet.GetContract(standard_contract)

        try:
            tx = self.wallet.MakeTransaction(tx=contract_tx,
                                             change_address=change_addr,
                                             fee=fee,
                                             from_addr=address_from)
        except ValueError:
            # if not enough unspents while fully synced
            raise JsonRpcError(-300, "Insufficient funds")
        except TXFeeError as e:
            raise JsonRpcError(-300, e)

        if tx is None:
            # if not enough unspents while not being fully synced
            raise JsonRpcError(-300, "Insufficient funds")
        data = standard_contract.Data
        tx.Attributes = [
            TransactionAttribute(usage=TransactionAttributeUsage.Script,
                                 data=data)
        ]
        context = ContractParametersContext(
            tx, isMultiSig=signer_contract.IsMultiSigContract
        )
        self.wallet.Sign(context)
        if context.Completed:
            tx.scripts = context.GetScripts()
            self.wallet.SaveTransaction(tx)
            NodeLeader.Instance().Relay(tx)
            return tx.ToJson()
        else:
            return context.ToJson()

    def get_blockheader_output(self, blockheader, params):

        if len(params) >= 2 and params[1]:
            jsn = blockheader.ToJson()
            jsn['confirmations'] = Blockchain.Default().Height - blockheader.Index + 1
            hash = Blockchain.Default().GetNextBlockHash(blockheader.Hash)
            if hash:
                jsn['nextblockhash'] = '0x%s' % hash.decode('utf-8')
            return jsn

        return Helper.ToArray(blockheader).decode('utf-8')
