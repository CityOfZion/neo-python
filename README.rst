.. raw:: html
    <p align="center">
      <img
        src="http://res.cloudinary.com/vidsy/image/upload/v1503160820/CoZ_Icon_DARKBLUE_200x178px_oq0gxm.png"
        width="125px;">
    </p>

    <h1 align="center">neo-python</h1>

    <p align="center">
      Python Node and SDK for the <b>NEO</b> blockchain.
    </p>

    <p align="center">
      <a href="https://pypi.python.org/pypi/neo-python">
        <img src="https://img.shields.io/pypi/v/neo-python.svg">
      </a>
      <a href="https://travis-ci.org/CityOfZion/neo-python">
        <img src="https://travis-ci.org/CityOfZion/neo-python.svg?branch=master">
      </a>
      <a href="https://neo-python.readthedocs.io/en/latest/?badge=latest" rel="nofollow">
        <img src="https://readthedocs.org/projects/neo-python/badge/?version=latest">
      </a>
      <a href='https://coveralls.io/github/CityOfZion/neo-python?branch=master'>
        <img src='https://coveralls.io/repos/github/CityOfZion/neo-python/badge.svg?branch=master' alt='Coverage Status' />
      </a>
    </p>



Overview
--------

What does it currently do
~~~~~~~~~~~~~~~~~~~~~~~~~

-  This project aims to be a full port of the original C# `NEO
   project <https://github.com/neo-project>`__
-  Run a Python based P2P node
-  Interactive CLI for configuring node and inspecting blockchain
-  Build, deploy, and run smart contracts
-  Runs smart contracts on the blockchain in a Python virtual machine
-  Very basic Wallet functionality (not fully tested, please do not use
   on mainnet)
-  `NEP2 <https://github.com/neo-project/proposals/blob/master/nep-2.mediawiki%3E>`__
   and
   `NEP5 <https://github.com/neo-project/proposals/blob/master/nep-5.mediawiki>`__
   compliant wallet functionality
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
Docs <https://neo-python.readthedocs.io/en/latest/>`__.

Get help or give help
~~~~~~~~~~~~~~~~~~~~~

-  Open a new
   `issue <https://github.com/CityOfZion/neo-python/issues/new>`__ if
   you encounter a problem.
-  Or ping **@localhuman** or **@metachris** on the `NEO
   Discord <https://discord.gg/R8v48YA>`__.
-  Pull requests welcome. You can help with wallet functionality,
   writing tests or documentation, or on any other feature you deem
   awesome.

Getting started
---------------

neo-python has two System dependencies (everything else is covered with
``pip``):

-  `LevelDB <https://github.com/google/leveldb>`__
-  `Python
   3.6+ <https://www.python.org/downloads/release/python-364/>`__ (3.5
   and below is not supported)

We have published a Youtube
`video <https://www.youtube.com/watch?v=ZZXz261AXrM>`__ to help get you
started. There are many more videos under the
`CityOfZion <https://www.youtube.com/channel/UCzlQUNLrRa8qJkz40G91iJg>`__
Youtube channel, check them out.

Docker
------

Using Docker is another option to run neo-python. There are example
Dockerfiles provided in the
`/docker folder <https://github.com/CityOfZion/neo-python/tree/development/docker>`__,
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

Ubuntu starting at 16.10 supports Python 3.6 in the official
repositories, and you can just install Python 3.6 and all the system
dependencies like this:

::

    apt-get install python3.6 python3.6-dev python3.6-venv python3-pip libleveldb-dev libssl-dev g++

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

Help needed. Installing the Python package plyvel seems to require C++
compiler support tied to Visual Studio and libraries. Refer to
`documentation <https://neo-python.readthedocs.io/en/latest/installwindows.html>`__.

Currently you probably should use the Linux subsystem with Ubuntu, or a
Virtual Machine with Linux. You can find more information and a guide
for setting up the Linux subsystem
`here <https://medium.com/@gubanotorious/installing-and-running-neo-python-on-windows-10-284fb518b213>`__.

Python 3.6
~~~~~~~~~~

neo-python is compatible with **Python 3.6 and later**.

On \*nix systems, install Python 3.6 via your package manager, or
download an installation package from the `official
homepage <https://www.python.org/downloads/release/python-364/>`__.


Install
~~~~~~~

It is recommended to put all project dependencies into its own virtual
environment, this way we don't pollute the global installation which
could lead to version conflicts.


1. Install from Github:

  ::

    git clone https://github.com/CityOfZion/neo-python.git
    cd neo-python

    # create virtual environment and activate

    python3.6 -m venv venv # this can also be python3 -m venv venv depending on your environment
    source venv/bin/activate

    # install the package in an editable form
    (venv) pip install -e .

2. Install from PyPi

  ::

    # create project dir
    mkdir myproject
    cd myproject

    # create virtual environment and activate

    python3.6 -m venv venv # this can also be python3 -m venv venv depending on your environment
    source venv/bin/activate

    (venv) pip install neo-python




Running
-------

After installing requirements and activating the environment, there is
an easy to use CLI (``np-prompt``) that starts the node and allows some
basic interactivity.

::

    np-prompt
    NEO cli. Type 'help' to get started

    neo> state
    Progress: 1054913 / 1237188

    neo>

By default, the CLI connects to the **TestNet** (see below how to switch
to MainNet or PrivNet).

Let's query for a block in the current server by hash or by block index:

::

    np-prompt
    NEO cli. Type 'help' to get started

    neo> block 122235
    {
        "index": 122235,
        "script": "",
        "merkleroot": "1d5a895ea34509a83becb5d2f9391018a3f59d670d94a2c3f8deb509a07464bd",
        "previousblockhash": "98ae05cb68ab857659cc6c8379eb7ba68b57ef1f5317904c295341d82d0a1713",
        "tx": [
            "1d5a895ea34509a83becb5d2f9391018a3f59d670d94a2c3f8deb509a07464bd"
        ],
        "version": 0,
        "time": 1479110368,
        "hash": "74671375033f506325ef08d35632f74083cca564dc7ea6444c94d3b9dec3f61b",
        "consensus data": 16070047272025254767,
        "next_consensus": "59e75d652b5d3827bf04c165bbe9ef95cca4bf55"
    }
    neo>

Bootstrapping the Blockchain
----------------------------

If you use neo-python for the first time, you need to synchronize the
blockchain, which may take a long time. Included in this project is the script
``np-bootstrap`` to automatically download a chain directory for you. To
bootstrap for testnet, run ``np-bootstrap``, get a cup of coffee
and wait. To bootstrap for mainnet, use ``np-bootstrap -m`` and
get 8 cups of coffee (3.3 GB file).

Important: do not use the chain files from
https://github.com/CityOfZion/awesome-neo.git, they will not work with
neo-python.

Available Wallet commands
~~~~~~~~~~~~~~~~~~~~~~~~~

::

    np-prompt
    NEO cli. Type 'help' to get started

    neo> help

    create wallet {wallet_path}
    open wallet {wallet_path}

    wallet { verbose } { rebuild } {rebuild BLOCK_HEIGHT}
    export wif { ADDRESS }
    import wif { WIF }

    send { ASSET_ID } { ADDRESS } { AMOUNT }

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
      --version             show program's version number and exit

Logging
~~~~~~~

Currently, ``np-prompt`` logs to ``prompt.log``

--------------

Tests
-----

Note that some of the unit tests use a giant blockchain fixture database
(~800MB). This file is not kept in the repo, but are downloaded the
first time the tests are run, this can take some time (depending on the
internet connection), but happens only once.

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

-  Double-check that you are using Python 3.6.x
-  Update the project dependencies (``pip install -e .``)
-  If you encounter any problems, please take a look at the
   `installation
   section <https://neo-python.readthedocs.io/en/latest/install.html#further-install-notes>`__
   in the docs, and if that doesn't help open an issue. We'll try to
   help.
-  You can reach us on the `NEO Discord <https://discord.gg/R8v48YA>`__,
   or simply file a `GitHub
   issue <https://github.com/CityOfZion/neo-python/issues/new>`__.

License
-------

-  Open-source
   `MIT <https://github.com/CityOfZion/neo-python/blob/master/LICENSE.md>`__.
-  Main author is [@localhuman](https://github.com/localhuman).

Donations
---------

Accepted at **ATEMNPSjRVvsXmaJW4ZYJBSVuJ6uR2mjQU**
