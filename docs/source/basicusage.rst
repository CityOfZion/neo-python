Basic Usage
-----------

There are two main ways to use neo-python: ``np-prompt`` and running just the node with custom
code.

np-prompt
"""""""""

Start np-prompt on TestNet:

::

    $ np-prompt

Show help with all available arguments:

::

    $ np-prompt -h
    usage: np-prompt [-h] [-m | -p [host] | --coznet | -c CONFIG]
                     [-t {dark,light}] [-v] [--datadir DATADIR] [--version]

    optional arguments:
      -h, --help            show this help message and exit
      -m, --mainnet         Use MainNet instead of the default TestNet
      -p [host], --privnet [host]
                            Use a private net instead of the default TestNet,
                            optionally using a custom host (default: 127.0.0.1)
      --coznet              Use the CoZ network instead of the default TestNet
      -c CONFIG, --config CONFIG
                            Use a specific config file
      -t {dark,light}, --set-default-theme {dark,light}
                            Set the default theme to be loaded from the config
                            file. Default: 'dark'
      -v, --verbose         Show smart-contract events by default
      --datadir DATADIR     Absolute path to use for database directories
      --version             show program's version number and exit


Node with custom code
"""""""""""""""""""""

Take a look at the examples in the ``/examples`` directory: https://github.com/CityOfZion/neo-python/tree/development/examples

See also the sections about "Settings and Logging" and "Interacting with Smart Contracts".


API server (JSON and/or REST)
""""""""""""""""""""""""""""""

Start JSON and REST API Server on Mainnet:

::

    $ np-api-server --mainnet --port-rpc 10332 --port-rest 80

Example notifications plus help with all available arguments:

::

  $ np-api-server --testnet --port-rpc 8080 --port-rest 8088
  [I 180315 09:27:09 NotificationDB:44] Created Notification DB At /Users/thomassaunders/.neopython/Chains/Test_Notif
  [I 180315 09:27:09 threading:864] [TestNet] Block 5644 / 53999
  [I 180315 09:27:09 np-api-server:11] Starting json-rpc api server on http://0.0.0.0:8080
  [I 180315 09:27:09 _observer:131] Site starting on 8080
  [I 180315 09:27:09 _observer:131] Starting factory <twisted.web.server.Site object at 0x110619828>
  [I 180315 09:27:09 np-api-server:11] Starting REST api server on http://0.0.0.0:8088

  # view help
  $ np-api-server -h
  usage: np-api-server [-h]
                     (--mainnet | --testnet | --privnet | --coznet | --config CONFIG)
                     [--port-rpc PORT_RPC] [--port-rest PORT_REST]
                     [--logfile LOGFILE] [--syslog] [--syslog-local [0-7]]
                     [--disable-stderr] [--datadir DATADIR]
                     [--maxpeers MAXPEERS] [--wallet WALLET] [--host HOST]

    optional arguments:
    -h, --help            show this help message and exit
    --datadir DATADIR     Absolute path to use for database directories
    --maxpeers MAXPEERS   Max peers to use for P2P Joining
    --wallet WALLET       Open wallet. Will allow you to use methods that
                          require an open wallet
    --host HOST           Hostname ( for example 127.0.0.1)

    Network options:
    --mainnet             Use MainNet
    --testnet             Use TestNet
    --privnet             Use PrivNet
    --coznet              Use CozNet
    --config CONFIG       Use a specific config file

    Mode(s):
    --port-rpc PORT_RPC     port to use for the json-rpc api (eg. 10332)
    --port-rest PORT_REST   port to use for the rest api (eg. 80)

    Logging options:
    --logfile LOGFILE     Logfile
    --syslog              Log to syslog instead of to log file ('user' is the
                          default facility)
    --syslog-local [0-7]  Log to a local syslog facility instead of 'user'.
                          Value must be between 0 and 7 (e.g. 0 for 'local0').
    --disable-stderr      Disable stderr logger


Port Description
""""""""""""""""""""""""""""""

If you want an external program to access your API server, an open firewall port is required. The following is a port description that can be set to fully open or open-on-demand.

.. list-table:: Port Description
   :widths: 20 10 10
   :header-rows: 1
   
   * - 
     - Main Net
     - Test Net
   * - JSON-RPC via HTTPS
     - 10331
     - 20331
   * - JSON-RPC via HTTP 
     - 10332 
     - 20332


Running an API Server using Windows WSL (Ubuntu)
""""""""""""""""""""""""""""""""""""""""""""""""

If you are running neo-python on Windows WSL (Ubuntu), opening the respective ports on your router is not enough.
You will need to add a new inbound rule to your Windows Firewall as described `here <https://www.nextofwindows.com/allow-server-running-inside-wsl-to-be-accessible-outside-windows-10-host>`_.
