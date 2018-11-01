import os
import inspect
import pkgutil
from importlib import import_module
from neo.api.JSONRPC.JsonRpcApi import JsonRpcApi
from neo.api.JSONRPC.ExtendedRpcCommand import ExtendedRpcCommand
import neo.api.JSONRPC.extended_commands as rpc_plugins

plugins = []


def iter_namespace(ns_pkg):
    return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")


# search in the plugins dir
for (importer, _name, ispkg) in iter_namespace(rpc_plugins):
    # only for plugins in packages
    if ispkg:
        # load the package
        m = importer.find_module(_name).load_module(_name)
        # and iterate over its contents
        for (_, mod_name, _) in iter_namespace(m):
            try:
                imported_module = import_module(mod_name)

                for i in dir(imported_module):
                    attribute = getattr(imported_module, i)

                    # to find a class that extends ExtendedRpcCommand
                    if inspect.isclass(attribute) and issubclass(attribute, ExtendedRpcCommand):
                        plugins.append(attribute)

            except ImportError:
                pass


class ExtendedJsonRpcApi(JsonRpcApi):
    """
    Extended JSON-RPC API Methods
    """

    def __init__(self, port, wallet=None):
        super(ExtendedJsonRpcApi, self).__init__(port, wallet)
        self.commands = {}
        for plugin in plugins:
            for command in plugin.commands():
                self.commands.update({command: plugin})

    def json_rpc_method_handler(self, method, params):
        plugin = self.commands.get(method)
        if plugin:
            return plugin.execute(self, method, params)
        else:
            return super(ExtendedJsonRpcApi, self).json_rpc_method_handler(method, params)
