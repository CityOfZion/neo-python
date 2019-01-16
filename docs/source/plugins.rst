Plugins
-------

At the moment ``neo-python`` supports Django style plugins for the REST and RPC server. Over time we expect to support loading more components in a similar fashion.


Plugable RPC and REST servers
"""""""""""""""""""""""""""""
The ``protocol.<netname>.json`` files have 2 keys to configure which specific class to load when using the ``np-api-server`` command.
::

    "RestServer": "neo.api.REST.RestApi.RestApi",
    "RPCServer": "neo.api.JSONRPC.JsonRpcApi.JsonRpcApi"

The format above can be read as
::

    'neo.<package>.<package>.<module>.<class name>'


The plugin loader will attempt to read these keys and use the values. If the keys are not present it will load the build servers instead.
It is possible to install alternative servers/plugins via pip and have them loaded. Just make sure to specify the path and class as shown above.

An example plugin can be found here: https://github.com/ixje/neopython-extended-rpc-server/
The example is an RPC server that extends the build JSON RPC Server. It supports loading of additional RPC commands via plugins.

