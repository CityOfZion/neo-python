Settings and Logging
====================

neo-python has a settings module which you can use to configure several things:

* The network: MainNet, TestNet, private networks or custom configs
* Logging:

  * Smart contract event logging
  * Logfile (optionally rotating)
  * Loglevel


To change settings, you have to import the settings instance like this:

::

    from neo.Settings import settings


Setting the network
"""""""""""""""""""

You can use the following settings methods to configure the network:

::

    settings.setup_mainnet()
    settings.setup_testnet()
    settings.setup_privnet()
    settings.setup(config_file)

By default, ``neo-python`` uses the TestNet.


Where to save data:
"""""""""""""""""""

By default, ``neo-python`` saves chain data at ``~/.neopython/Chains``.  If you would like to change this, you can pass the ``--datadir`` flag to any of the commands (``np-prompt``, ``np-api-server``,``np-bootstrap``) to specify where the ``Chains`` directory should be placed.
You can also set this manually via the ``settings`` module like so:

.. code-block:: sh

  settings.set_data_dir('your/path')




Logging
"""""""

neo-python uses the following defaults:

* all events from all smart contracts are logged with loglevel INFO
* loglevel is set to INFO
* logging to a logfile is deactivated (prompt.py logs to prompt.log)


Smart Contract Events
---------------------

If you want to disable logging of all smart contract events, you can do so:

::

    settings.set_log_smart_contract_events(False)


Changing the loglevel
---------------------

To change the loglevel (eg. to also show DEBUG logs, or to only show ERRORS):

::

    import logging

    # Show everything, including debug logs:
    settings.set_loglevel(logging.DEBUG)

    # Only show errors:
    settings.set_loglevel(logging.ERROR)


Changing in the prompt
----------------------

To change the loglevel in the ``prompt`` interface, use the following command

.. code-block:: sh

  neo> config sc-events on
  neo> config sc-events off


Configuring a logfile
---------------------

To enable logging to a logfile:

::

    # Just a single logfile, with no limits or rotation:
    settings.set_logfile(your_logfile_path)

    # To enable rotation with a maximum of 10MB per file and 3 rotations:
    settings.set_logfile(your_logfile_path, 1e7, 3)


Logging in custom code
----------------------

neo-python is using `logzero <https://logzero.readthedocs.io>`_ for logging. To use a
logger with the existing neo logging configuration, you can just import the logger from logzero:

::

    from logzero import logger

    # These log messages are sent to the console
    logger.debug("hello")
    logger.info("info")
    logger.warn("warn")
    logger.error("error")

    # This is how you'd log an exception
    try:
        raise Exception("this is a demo exception")
    except Exception as e:
        logger.exception(e)
