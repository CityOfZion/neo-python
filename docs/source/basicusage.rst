Basic Usage
-----------

There are two main ways to use neo-python: ``prompt.py`` and running just the node with custom
code.

prompt.py
"""""""""

Start prompt.py on TestNet:

::

    $ python prompt.py

Show help with all available arguments:

::

    $ python prompt.py -h
    usage: prompt.py [-h] [-m] [-p] [-c CONFIG] [-t {dark,light}] [--version]

    optional arguments:
    -h, --help            show this help message and exit
    -m, --mainnet         Use MainNet instead of the default TestNet
    -p, --privnet         Use PrivNet instead of the default TestNet
    -c CONFIG, --config CONFIG
                            Use a specific config file
    -t {dark,light}, --set-default-theme {dark,light}
                            Set the default theme to be loaded from the config
                            file. Default: 'dark'
    --version             show program's version number and exit



Node with custom code
"""""""""""""""""""""

Take a look at the examples in the ``/examples`` directory: https://github.com/CityOfZion/neo-python/tree/development/examples

See also the sections about "Settings and Logging" and "Interacting with Smart Contracts".
