Changelog
=========

All notable changes to this project are documented in this file.

[0.6.2-dev] in progress
-----------------------
- ...


[0.6.1] 2018-03-16
----------------------------
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
----------------------------
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
