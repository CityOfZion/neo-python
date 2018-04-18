Changelog
=========

All notable changes to this project are documented in this file.

[0.6.8-dev] in progress
-----------------------
- add ``ServiceEnabled`` boolean to settings to determine whether nodes should send other nodes blocks
- updated new block retrieval mechanism
- fix for token_delete command not removing tokens from wallet file
- fixed sc-events and notification DB showing previous block height instead of final block height of event
- persist refund() notify events in notification DB


[0.6.7] 2018-04-06
-----------------------
- Update all the requirements
- added ``--maxpeers`` option for ``np-prompt`` and ``np-api-server``.  This allows p2p discovery of new nodes up to the value specified
- added ``--host`` option for ``np-api-server`` in order to specify a hostname for the server
- added more testing for ``neo.Network`` module
- various networking improvements
- fix in ``neo.SmartContract.StateReader`` ``ContractMigrate`` functionality
- added check for Python 3.6 on startup
- API: Added CORS header ``Access-Control-Allow-Headers: 'Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With'`` (fixes ``Request header field Content-Type is not allowed by Access-Control-Allow-Headers in preflight response``)


[0.6.6] 2018-04-02
------------------
- add ``Neo.Runtime.Serialize`` and ``Neo.Runtime.Deserialize`` for compliance with this (`#163 <https://github.com/neo-project/neo/pull/163>`_)
- Fixed IsWalletTransaction to make it compare scripts in transactions to scripts (instead of scripthashes) in wallet contracts and scripthashes of transactions (instead of scripts) to scripthashes of watch-only addresses
- Python version check in ``Settings.py``: fail if not Python 3.6+ (can be disabled with env var ``SKIP_PY_CHECK``)


[0.6.5] 2018-03-31
-----------------------
- Changed the ``eval()`` call when parsing the `--tx-attr` param to parse only json. Reduced the surface and options available on the other 2 eval calls to improve security.
- fix wallet rebuild database lock errors (`PR #365 <https://github.com/CityOfZion/neo-python/pull/365>`_)
- Fixed `synced_watch_only_balances` being always zero issue (`#209  <https://github.com/CityOfZion/neo-python/issues/209>`_)
- Added 'getpeers' to the JSON RPC API (only containing the available functionality)
- Updated to neo-boa==0.4.0, which has support for using dictionaries and interactive debugging
- Added interactive VM Debugger `#367 <https://github.com/CityOfZion/neo-python/pull/367>`_
- Added ``Pause`` and ``Resume`` methods to ``neo.Core.Blockchain`` in order to allow for processing to occur without new incoming blocks
- Fix bug with checking if contract is an NEP5 Token
- Update testnet bootstrap files
- lowered amount of blocks requested by each thread to prevent hanging connections


[0.6.4] 2018-03-24
------------------
- Add GZIP compression to RPC server responses if the caller supports it.
- Change VM fault reporting to only happen when debug logging is enabled
- fix engine error states
- update mainnet bootstrap files
- performance fix for VM engine execution logging (`PR #354 <https://github.com/CityOfZion/neo-python/pull/354>`_)


[0.6.3] 2018-03-21
------------------
- update to ``neocore==0.3.10`` to fix ``ToNeoJsonString()`` issue `identified here <https://github.com/CityOfZion/neo-python/issues/349>`_
- make home dir optional for ``.neopython``
- performance fix for block update speed


[0.6.2] 2018-03-21
------------------
- Implementing interop type ``MAP`` along with new opcodes ``NEWMAP HASKEY KEYS VALUES`` and modify ``ARRAYSIZE PICKITEM SETITEM REMOVE`` to support ``MAP`` as `per PR here <https://github.com/neo-project/neo-vm/pull/28>__`
- Added support for using ``--from-addr=`` to specify the address to use for ``testinvoke`` in ``prompt.py``. (`PR #329 <https://github.com/CityOfZion/neo-python/pull/329>`_)
- Fixed ``neo/bin/prompt.py`` to redact WIF keys, nep2 keys and contract metadata from the command history file ``.prompt.py.history``.
- Added TransactionInvocation.GetScript to ``StateReader.py``
- Fixed missing uri locations in ``neo/api/REST/RestApi.py`` (`PR #342 <https://github.com/CityOfZion/neo-python/pull/342>`_)
- Fixed privatenet check by fixing the chain path for checks in Settings (`PR #341 <https://github.com/CityOfZion/neo-python/pull/341>`_)
- Fixed ``neo-privnet.sample.wallet``
- Fix for current block height lag behind other RPC implementations by 1-3 blocks
- Fixed ``bootstrap.py`` to use the specified data directory, instead of hard-coded relative paths.
- Test chains moved to the user data directory, instead of the projects code path.


[0.6.1] 2018-03-16
------------------
- Fixed README reference in ``MANIFEST.in``
- Added additional error messages to ``ExecutionEngine.py`` to help with debugging smart contracts.
- Changes for Pypi compatibility:
  - move protocol.*.json to ``neo/data/``
  - move ``prompt.py`` and other scripts to ``neo/bin``
  - default chain data path is now in ``~/.neopython/Chains``.  ``prompt.log`` and ``prompt.history`` files are also stored there
  - the following console scripts are now on the ``venv`` path after running ``pip install neo-python`` or ``pip install -e .`` for github based installs:
    - ``np-prompt``
    - ``np-api-server``
    - ``np-bootstrap``
    - ``np-reencrypt-wallet``
  - updated docs for Pypi changes


[0.5.7] 2018-03-14
------------------
- update to ``neocore==0.3.8``
- Fixed README reference in ``MANIFEST.in``, add pypi badge to readme
- Add ability to specify ``--datadir`` path for where leveldb directories are stored
- Tries to auto-create ``Chains`` directory in ``--datadir`` if it doesnt exist
- Add scripts to be exported for package install.  ``np_prompt``, ``np_api_server``, ``np_bootstrap``, and ``np_reencrypt_wallet`` available as commands after ``pip`` install
- add protocol.*.json into data package
- move ``neo-privnet.wallet`` to ``neo-privnet.sample.wallet`` and .gitignore ``neo-privnet.wallet``
- Change ``README.md`` to `README.rst``


[0.5.4] 2018-03-14
------------------
- All requests to the API that are invalid will now receive a ``None`` for results rather than an empty list ``[]``
- update to neo-boa==0.3.7
- `api-server.py <https://github.com/CityOfZion/neo-python/blob/development/api-server.py>`_: Improved logging setup. See the options with ``./api-server.py -h``
- Added ``sc-debug-notify`` option to the ``config`` console command. This preserves smart contract ``Notify()`` events when SC execution fails and is intended for SC debugging purposes only.
- Added VM instruction counter to ``ExecutionEngine.py`` error messages to indicate the final instruction that failed. Allows for setting conditional breakpoints to support SC debugging.
- Renamed ``neo.api.REST.NotificationRestApi`` to ``neo.api.REST.RestApi``
- Added ``-v/--verbose`` argument to prompt.py, which makes prompt.py show smart contract events by default
- Added ``vm-log`` option to the ``config`` console command. This enabled logging of VM instructions to ``vm_instructions.log`` for debugging purposes.
- Fix multi-signature contract import to allow using a single signature
- Fix fund sending from multi-signature contract
- Added instructions on retrieving NEO TestNet funds
- Fixed issue with missing ``notifications/`` prefix for ``addr`` call in ``neo/api/REST/RestApi.py``
- Added ``neo-privnet.wallet`` to the project root. This is the standard wallet for `private networks <https://hub.docker.com/r/cityofzion/neo-privatenet/>`_.
- prompt.py: When using a privnet with ``-p``, check if chain database is correct. Renamed ``Chains/Priv_Notif`` to ``Chains/privnet_notif`` (if you need your old privnet notification db, you need to rename it manually).
- Optionally allow to use custom privnet hosts with ``-p`` (`PR #312 <https://github.com/CityOfZion/neo-python/pull/312>`_)
- Added a dependency check to ``Settings.py``, which verifies that the installed dependencies match those in requirements.txt


[0.5.3] 2018-03-04
------------------
- add documentation for data types in ``neo-python``
- add intructions on ``build``, ``build .. test``, ``import contract``, and ``testinvoke`` to docs
- ``BuildNRun`` results now converted to ``ContractParameter`` before printed
- ``contract {hash}`` no longer throws errors when it is not an ``NEP5`` contract
- Added method ``AsParameterType`` to ``ContractParameter`` for casting results


[0.5.1] 2018-03-02
------------------
- Documentation and Dockerfile updates for Python 3.6
- Notification API: include peer count in status
- Fix token error handling (`cedde9ec <https://github.com/CityOfZion/neo-python/commit/cedde9ec131f738e0f6d97710f76b7cc019e0aa3>`_)
- Added warning about wallet syncing prior to logging insufficient funds error, added IsSynced method Wallet class to check this (`PR #2259 <https://github.com/CityOfZion/neo-python/pull/259>`_)


[0.5.0] 2018-03-01
------------------
- Move to Python 3.6 (`PR #270 <https://github.com/CityOfZion/neo-python/pull/270>`_)
    - move to only python 3.6+ support
    - use new version of compiler ( neo-boa==0.3.3 ) based on python 3.6 wordcode
    - full testing of VM and all compiled smart contracts
    - adds new command `TestBuild` for running tests of compiled contracts
- Add Notification REST URL prefix (`PR #274 <https://github.com/CityOfZion/neo-python/pull/274>`_)
- Add ``api-server.py`` (`PR #271 <https://github.com/CityOfZion/neo-python/pull/271>`_)
- Fixed script value returned by JSON-RPC invokes (`PR #268 <https://github.com/CityOfZion/neo-python/pull/268>`_)
- Added support for additional JSON-RPC "type" parameters (`PR #267 <https://github.com/CityOfZion/neo-python/pull/267>`_)
- Updating of almost all dependencies (`PR #261 <https://github.com/CityOfZion/neo-python/pull/261>`_)
- Fixed bug with transactions consuming between 9 and 10 GAS (`PR #260 <https://github.com/CityOfZion/neo-python/pull/260>`_)
- Added automatic deploy to pypi (`PR #275 <https://github.com/CityOfZion/neo-python/pull/275>`_)
- Updated Notification REST API URLs with ``/v1`` prefix, and some with ``/v1/notifications`` (`PR #274 <https://github.com/CityOfZion/neo-python/pull/274>`_)
- Fixed inconsistencies with JSON-RPC output values (`PR #272 <https://github.com/CityOfZion/neo-python/pull/272>`_)



[0.4.9] 2018-02-21
------------------
- wallet sync error and password fixes related to encryption changes (`PR #245 <https://github.com/CityOfZion/neo-python/pull/245>`_)
- import contract_addr and build ... test fixes (`PR #237 <https://github.com/CityOfZion/neo-python/pull/237>`_)
- Easy Coznet support(`PR #239 <https://github.com/CityOfZion/neo-python/pull/239>`_)
- ContractParameterContext fix (`PR #242 <https://github.com/CityOfZion/neo-python/pull/242>`_)
- Zero length bytearray in VM fix (`PR #244 <https://github.com/CityOfZion/neo-python/pull/244>`_)
- Wallet Encryption changes (`PR #232 <https://github.com/CityOfZion/neo-python/pull/232>`_)
- Close wallet on quit (`PR #226 <https://github.com/CityOfZion/neo-python/pull/226>`_)
- Bugfix for smart contract storage events (`PR #228 <https://github.com/CityOfZion/neo-python/pull/228>`_)


[0.4.8] 2018-02-15
------------------

- Fix Gas Cost Calculation (`PR #220 <https://github.com/CityOfZion/neo-python/pull/220>`_)
- Clarify message for token mint command (`PR #212 <https://github.com/CityOfZion/neo-python/pull/212>`_)
- Troubleshooting osx script (`PR #208 <https://github.com/CityOfZion/neo-python/pull/208>`_)
- Make Contract Search case insensitive (`PR #207 <https://github.com/CityOfZion/neo-python/pull/207>`_)
- implement a more robust CLI command parser
- added peristence to NotificationDB for NEP5 Tokens
- upstream neocore update


[0.4.6] 2018-01-24
------------------

- Added support for StateTransaction and StateDescriptors (`PR #193 <https://github.com/CityOfZion/neo-python/pull/193>`_)
- Allow multiple open wallets (`PR #185 <https://github.com/CityOfZion/neo-python/pull/185>`_)
- Added ability to include transaction attributes with the send command. example: ``send neo APRgMZHZubii29UXF9uFa6sohrsYupNAvx 10 --tx-attr={'usage':241,'data':'My Remark'}`` (`PR #184 <https://github.com/CityOfZion/neo-python/pull/184>`_)
- Notification REST API (`PR #177 <https://github.com/CityOfZion/neo-python/pull/177>`_, `examples/notification-rest-api-server.py <https://github.com/CityOfZion/neo-python/blob/development/examples/notification-rest-api-server.py>`_)
- Minor cleanups and documentation updates


[0.4.5] 2018-01-18
------------------

- updated ``neo-boa`` to ``0.2.2``, added support for array ``REMOVE`` VM opcodes
- moved core functions to `neocore <https://github.com/CityOfZion/neo-python-core>`_
- better LevelDB support for OSX
- dependency udates
- Makefile with some useful commands
- ability to claim GAS from SC address
- lots of documentation
- various small bugfixes


[0.4.3] 2017-12-21
------------------

- updated ``neo-boa`` to ``0.2.1``
- added support for array ``REVERSE`` and ``APPEND`` VM opcodes


[0.4.3] 2017-12-21
------------------

- updated ``neo-boa`` to ``0.2.1``
- added support for array ``REVERSE`` and ``APPEND`` VM opcodes


[0.4.2] 2017-12-18
------------------

- updated ``neo-boa`` to ``0.2.0``
- added support for `debug storage <https://github.com/CityOfZion/neo-python/pull/120>`_


[0.4.1] 2017-12-15
------------------

- added support for runtime notifications from verification contracts
- added support for checking verification during ``mintTokens`` invoke
- updated prompt help
- added additional SC Api ( ``Neo.Runtime.GetTime``, ``Neo.Transaction.GetUnspentCoins``, ``Neo.Header.GetIndex``)
- added support for dynamically defined smart contract execution
- added ability to alias an address in the wallet
- added support for pip versions >= 10.0
