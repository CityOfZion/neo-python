.. image:: http://res.cloudinary.com/vidsy/image/upload/v1503160820/CoZ_Icon_DARKBLUE_200x178px_oq0gxm.png
    :alt: CoZ logo

neo-python
----------

Python Node and SDK for the NEO blockchain.

.. image:: https://img.shields.io/pypi/v/neo-python.svg
    :target: https://pypi.python.org/pypi/neo-python
    :alt: Pypi
.. image:: https://travis-ci.org/CityOfZion/neo-python.svg?branch=master
    :target: https://travis-ci.org/CityOfZion/neo-python
    :alt: Travis CI
.. image:: https://readthedocs.org/projects/neo-python/badge/?version=latest
    :target: https://neo-python.readthedocs.io/en/latest/?badge=latest
    :alt: ReadTheDocs
.. image:: https://coveralls.io/repos/github/CityOfZion/neo-python/badge.svg?branch=master
    :target: https://coveralls.io/github/CityOfZion/neo-python?branch=master
    :alt: Coveralls



Overview
--------

What does it currently do
~~~~~~~~~~~~~~~~~~~~~~~~~

-  This project aims to be a full port of the original C# `NEO
   project <https://github.com/neo-project>`_
-  Run a Python based P2P node
-  Interactive CLI for configuring node and inspecting blockchain
-  Compile, test, deploy and run Smart Contracts written in Python or any smart contract in the ``.avm`` format
-  Runs smart contracts on the blockchain in a Python virtual machine
-  Very basic Wallet functionality (not fully tested, please do not use
   on mainnet)
-  `NEP2 <https://github.com/neo-project/proposals/blob/master/nep-2.mediawiki>`_
   and
   `NEP5 <https://github.com/neo-project/proposals/blob/master/nep-5.mediawiki>`_
   compliant wallet functionality
- `NEP-7 <https://github.com/neo-project/proposals/blob/master/nep-7.mediawiki>`_ and `NEP-8 <https://github.com/neo-project/proposals/blob/c20182cecd92102b9e5a3158a005762eefb8dbdf/nep-8.mediawiki>`_ support
-  RPC Client
-  RPC server
-  Notification Server ( for viewing transfers of NEP5 tokens )
-  ``Runtime.Log`` and ``Runtime.Notify`` event monitoring

What will it do
~~~~~~~~~~~~~~~

-  Consensus nodes
-  More robust smart contract debugging and inspection

Documentation
~~~~~~~~~~~~~

The full documentation on how to install, configure and use neo-python
can be found at `Read The
Docs <https://neo-python.readthedocs.io/en/latest/>`_.

Get help or give help
~~~~~~~~~~~~~~~~~~~~~

-  Open a new
   `issue <https://github.com/CityOfZion/neo-python/issues/new>`_ if
   you encounter a problem.
-  Or ping **@localhuman**, **@metachris** or **@ixje** on the `NEO
   Discord <https://discord.gg/R8v48YA>`_.
-  Pull requests welcome. Have a look at the issue list for ideas.
   You can help with wallet functionality, writing tests or documentation,
   or on any other feature you deem awesome.

Getting started
---------------

neo-python has two System dependencies (everything else is covered with
``pip``):

-  `LevelDB <https://github.com/google/leveldb>`_
-  `Python
   3.6 <https://www.python.org/downloads/release/python-366/>`_ or `Python 3.7 <https://www.python.org/downloads/release/python-370/>`_ (3.5 and below is not supported)

We have published a Youtube
`video <https://www.youtube.com/watch?v=ZZXz261AXrM>`_ to help get you
started. There are many more videos under the
`CityOfZion <https://www.youtube.com/channel/UCzlQUNLrRa8qJkz40G91iJg>`_
Youtube channel, check them out.

Docker
------

Using Docker is another option to run neo-python. There are example
Dockerfiles provided in the
`/docker folder <https://github.com/CityOfZion/neo-python/tree/development/docker>`_,
and we have an image on Docker hub, tagged after the neo-python
releases: https://hub.docker.com/r/cityofzion/neo-python/

Native installation
-------------------

Instructions on the system setup for neo-python:

LevelDB
~~~~~~~

OSX
^^^

::

    brew install leveldb

Ubuntu/Debian 16.10+
^^^^^^^^^^^^^^^^^^^^

Ubuntu starting at 16.10 supports Python 3.6+ in the official repositories.

First, ensure Ubuntu is fully up-to-date with this:

::

   sudo apt-get update && sudo apt-get upgrade

You can install Python 3.7 and all the system dependencies like this:

::

   sudo apt-get install python3.7 python3.7-dev python3.7-venv python3-pip libleveldb-dev libssl-dev g++


Or, you can install Python 3.6 and all the system dependencies like this:

::

    sudo apt-get install python3.6 python3.6-dev python3.6-venv python3-pip libleveldb-dev libssl-dev g++

Older Ubuntu versions (eg. 16.04)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For older Ubuntu versions you'll need to use an external repository like
Felix Krull's deadsnakes PPA at
https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa (read more
`here <https://askubuntu.com/questions/865554/how-do-i-install-python-3-6-using-apt-get>`__).

(The use of the third-party software links in this documentation is done
at your own discretion and risk and with agreement that you will be
solely responsible for any damage to your computer system or loss of
data that results from such activities.)

::

    apt-get install software-properties-common python-software-properties
    add-apt-repository ppa:deadsnakes/ppa
    apt-get update
    apt-get install python3.6 python3.6-dev python3.6-venv python3-pip libleveldb-dev libssl-dev g++

Centos/Redhat/Fedora
^^^^^^^^^^^^^^^^^^^^

::

    # Install Python 3.6:
    yum install -y centos-release-scl
    yum install -y rh-python36
    scl enable rh-python36 bash

    # Install dependencies:
    yum install -y epel-release
    yum install -y readline-devel leveldb-devel libffi-devel gcc-c++ redhat-rpm-config gcc python-devel openssl-devel

Windows
^^^^^^^

Currently, you should use the Linux subsystem with Ubuntu, or a
Virtual Machine with Linux. You can find more information and a guide
for setting up the Linux subsystem
`here <https://medium.com/@gubanotorious/installing-and-running-neo-python-on-windows-10-284fb518b213>`__.

Installing "Ubuntu" from Microsoft Store installs Ubuntu 16.04. You should install Ubuntu 18.04 from Microsoft Store found here: https://www.microsoft.com/en-us/p/ubuntu-1804/9n9tngvndl3q?activetab=pivot%3aoverviewtab

Help needed for running natively. Installing the Python package plyvel seems to require C++
compiler support tied to Visual Studio and libraries. Refer to
`documentation <https://neo-python.readthedocs.io/en/latest/installwindows.html>`__.

Python 3.6+
~~~~~~~~~~~

neo-python is compatible with **Python 3.6 and later**.

On \*nix systems, install Python 3.6 or Python 3.7 via your package manager, or
download an installation package from the `official
homepage <https://www.python.org/downloads/>`__.


Install
~~~~~~~

It is recommended to put all project dependencies into its own virtual
environment, this way we don't pollute the global installation which
could lead to version conflicts.


1. Install from Github:

  ::

    git clone https://github.com/CityOfZion/neo-python.git
    cd neo-python

    # if you want to use the development branch, switch now
    git checkout development

    # create virtual environment using Python 3.7 and activate or skip to the next step for Python 3.6
    python3.7 -m venv venv
    source venv/bin/activate

    # create virtual environment using Python 3.6 and activate
    python3.6 -m venv venv
    source venv/bin/activate

    # install the package in an editable form
    (venv) pip install wheel -e .

2. Install from PyPi

  ::

    # create project dir
    mkdir myproject
    cd myproject

    # create virtual environment using Python 3.7 and activate or skip to the next step for Python 3.6
    python3.7 -m venv venv
    source venv/bin/activate

    # create virtual environment using Python 3.6 and activate
    python3.6 -m venv venv
    source venv/bin/activate

    (venv) pip install wheel neo-python


Running
-------

After installing requirements and activating the environment, there is
an easy to use CLI (``np-prompt``) that starts the node and allows some
basic interactivity.

::

    np-prompt
    NEO cli. Type 'help' to get started

    neo> show state
    Progress: 10926 / 11145
    Block-cache length 0
    Blocks since program start 0
    Time elapsed 0.02598465 mins
    Blocks per min 0
    TPS: 0

    neo>

By default, the CLI connects to the **TestNet** (see below how to switch
to MainNet or PrivNet).

Let's query for a block in the current server by hash or by block index:

::

    np-prompt
    NEO cli. Type 'help' to get started

    neo> show block 122235
    {
        "hash": "0xf9d7bc6f337a6cbe124b92b90ad7b29e2628e78202ea2daa19ed93fdc779c0e6",
        "size": 686,
        "version": 0,
        "previousblockhash": "0x1f262a0979d6da0eabaaf54252fb2508564a99fee642a77ff0773671fe5fddb9",
        "merkleroot": "0x5d4f86734c2a53187aa96751b9180d69f85f9bd7875f2eb83a27666ad052ea1e",
        "time": 1496920870,
        "index": 122235,
        "nonce": "7847dea9df7571c1",
        "nextconsensus": "AdyQbbn6ENjqWDa5JNYMwN3ikNcA4JeZdk",
        "script": {
            "invocation": "40e5a7d23cb065308412d769ca2ba6dd974aa453d0c915c25a7d951488eaa6c4eff5bbe251f01725b959fb89e7dd631f7f41efd50897c466d75e8359154f6137bf402f690a98a44e5ecb22e7f20bb75bac40cac89f4805f4706ec9daf8e6ccc15def216d667423bb148e78db9461e288d7363f699741a0efb4c7c6c6dc902250cf3f4023ba2eb464aa8841cb2230c0f9f016a47c1e54e1f809da550743c33b0529b5996f4c5993a38bb73887e0b3fd7a093f6abd00d136048169a99cf34373560b8956408e816d0a0b018c348070da63f513b5b3332ef31914c420203b792f25048c1b8b397bc4bd47315be44491f7182be8aeca39035a2cd51a20da034820e5e1b5c0644052ce1cb6769e9dc9375ea96db8d538e6b2210a093c555f759ccf1d908f8c2fe3cf6236c4dade54ebca825a36e81049c7f4b149c1458c30b37460fc22581201f2",
            "verification": "55210209e7fd41dfb5c2f8dc72eb30358ac100ea8c72da18847befe06eade68cebfcb9210327da12b5c40200e9f65569476bbff2218da4f32548ff43b6387ec1416a231ee821034ff5ceeac41acf22cd5ed2da17a6df4dd8358fcb2bfb1a43208ad0feaab2746b21026ce35b29147ad09e4afe4ec4a7319095f08198fa8babbe3c56e970b143528d2221038dddc06ce687677a53d54f096d2591ba2302068cf123c1f2d75c2dddc542557921039dafd8571a641058ccc832c5e2111ea39b09c0bde36050914384f7a48bce9bf92102d02b1873a0863cd042cc717da31cea0d7cf9db32b74d4c72c01b0011503e2e2257ae"
        },
        "tx": [
            {
                "txid": "0x5d4f86734c2a53187aa96751b9180d69f85f9bd7875f2eb83a27666ad052ea1e",
                "size": 10,
                "type": "MinerTransaction",
                "version": 0,
                "attributes": [],
                "vout": [],
                "vin": [],
                "sys_fee": "0",
                "net_fee": "0",
                "scripts": [],
                "nonce": 3749016001
            }
        ]
    }
    neo>

Bootstrapping the Blockchain
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you use neo-python for the first time, you need to synchronize the
blockchain, which may take a long time. Included in this project is the script
``np-bootstrap`` to automatically download a chain directory for you.

np-bootstrap Usage
^^^^^^^^^^^^^^^^^^

::

    $ np-bootstrap -h
    usage: np-bootstrap [-h] [-m] [-c CONFIG] [-n] [-s] [--datadir DATADIR]

    optional arguments:
      -h, --help            show this help message and exit
      -m, --mainnet         use MainNet instead of the default TestNet
      -c CONFIG, --config CONFIG
                            Use a specific config file
      -n, --notifications   Bootstrap notification database
      -s, --skipconfirm     Bypass warning about overwritting data in Chains/SC234
      --datadir DATADIR     Absolute path to use for database directories

Bootrapping Testnet
^^^^^^^^^^^^^^^^^^^

To bootstrap the testnet blockchain, run ``np-bootstrap``, get a cup of coffee
and wait. Then, bootstrap the testnet notifications database with ``np-bootstrap -n``.

Bootstrapping Mainnet
^^^^^^^^^^^^^^^^^^^^^

To bootstrap the mainnet blockchain, run ``np-bootstrap -m`` and get 8 cups of coffee
(9+ GB file). Then, bootstrap the mainnet notifications database with
``np-bootstrap -m -n``.

**Important:** do not use the chain files from
https://github.com/CityOfZion/awesome-neo.git, they will not work with
neo-python.

Basic Wallet commands
~~~~~~~~~~~~~~~~~~~~~

::

    wallet create {wallet_path}
    wallet open {wallet_path}
    wallet close

    wallet (verbose)
    wallet rebuild (start block)

    wallet import wif {wif}
    wallet export wif {address}

    wallet send {args}       # (NEO/GAS)
    wallet token send {args} # NEP5


For a complete list of commands use ``help``.

Running on MainNet
~~~~~~~~~~~~~~~~~~

To run the prompt on MainNet, you can use the CLI argument ``-m`` (eg.
``np-prompt -m``), for running on PrivNet you can use ``-p``. Be
sure to check out the details of the parameters:

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
      --maxpeers MAXPEERS   Max peers to use for P2P Joining
      --version             show program's version number and exit

Logging
~~~~~~~

Currently, ``np-prompt`` logs to ``prompt.log``


Tests
-----

Note we make use of a Blockchain fixture database (~15 MB). This file is not kept in the repo,
but is downloaded the first time the tests are run, this can take some time (depending on the internet connection),
but happens only once.

Useful commands
---------------

::

    make lint
    make test
    make coverage
    make docs


    # run only neo-python tests
    python -m unittest discover neo

    # run only neo-boa tests
    python -m unittest discover boa_test

Updating the version number and releasing new versions of neo-python
--------------------------------------------------------------------

This is a checklist for releasing a new version, which for now means:

1. Merging the changes from development into master
2. Setting the version from eg. ``0.4.6-dev`` to ``0.4.6`` (which
   automatically created a tag/release)
3. On the dev branch, setting the version to the next patch, eg.
   ``0.4.7-dev``
4. Pushing master, development and the tags to GitHub

Make sure you are on the development branch and have all changes merged
that you want to publish. Then follow these steps:

::

    # Only in case you want to increase the version number again (eg. scope changed from patch to minor):
    # bumpversion --no-tag minor|major

    # Update CHANGELOG.rst: make sure all changes are there and remove `-dev` from the version number
    vi CHANGELOG.rst
    git commit -m "Updated changelog for release" CHANGELOG.rst

    # Merge development branch into master
    git checkout master
    git merge development

    # Set the release version number and create the tag
    bumpversion release

    # Switch back into the development branch
    git checkout development

    # Increase patch number and add `-dev`
    bumpversion --no-tag patch

    # Push to GitHub, which also updates the PyPI package and Docker Hub image
    git push origin master development --tags

Troubleshooting
---------------

If you run into problems, check these things before ripping out your
hair:

-  Double-check that you are using Python 3.6.x or Python 3.7.x
-  Update the project dependencies (``pip install -e .``)
-  If you encounter any problems, please take a look at the
   `installation
   section <https://neo-python.readthedocs.io/en/latest/install.html#further-install-notes>`_
   in the docs, and if that doesn't help open an issue. We'll try to
   help.
-  You can reach us on the `NEO Discord <https://discord.gg/R8v48YA>`_,
   or simply file a `GitHub
   issue <https://github.com/CityOfZion/neo-python/issues/new>`_.

License
-------

-  Open-source
   `MIT <https://github.com/CityOfZion/neo-python/blob/master/LICENSE.md>`_.
-  Contributors: `@localhuman <https://github.com/localhuman>`_ (Creator), `@metachris <https://github.com/metachris>`_, `@ixje <https://github.com/ixje>`_, and `many more <https://github.com/CityOfZion/neo-python/graphs/contributors>`_

Donations
---------

Accepted at **ATEMNPSjRVvsXmaJW4ZYJBSVuJ6uR2mjQU**
