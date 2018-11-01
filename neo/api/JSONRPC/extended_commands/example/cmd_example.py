from neo.api.JSONRPC.JsonRpcApi import JsonRpcError
from neo.api.JSONRPC.ExtendedRpcCommand import ExtendedRpcCommand


# must inherit from ExtendedRpcCommand or the plugin will not be loaded
class ExampleCommand(ExtendedRpcCommand):

    @classmethod
    def commands(cls):
        return ["my_command", "my_command2"]

    @classmethod
    def execute(cls, json_rpc_api, method, params):
        if method == "my_command":
            if json_rpc_api.wallet:
                raise JsonRpcError(-1337, "Unsafe command with open wallet")
            else:
                return "first command success"
        elif method == "my_command2":
            return "second command success"
