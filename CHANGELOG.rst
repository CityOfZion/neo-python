Changelog
=========

All notable changes to this project are documented in this file.

[0.4.9] 2018-02-21
----------------------------
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
