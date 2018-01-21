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

## Overview

### What does it currently do

- This project aims to be a full port of the original C#
[NEO project](https://github.com/neo-project)
- Run a Python based P2P node
- Interactive CLI for configuring node and inspecting blockchain
- Runs smart contracts on the blockchain in a Python virtual machine
- Very basic Wallet functionality (not fully tested, please do not use on mainnet)
- [NEP2](https://github.com/neo-project/proposals/blob/master/nep-2.mediawiki>) and [NEP5](https://github.com/neo-project/proposals/blob/master/nep-5.mediawiki) compliant wallet functionality
- RPC Client
- ``Runtime.Log`` and ``Runtime.Notify`` event monitoring


### What will it do

- RPC server
- Consensus nodes
- More robust smart contract debugging and inspection

### Documentation

- Installation, Configuration, and usage documentation available at [Read The Docs](https://neo-python.readthedocs.io/en/latest/)

### Get Help or give help

- Open a new [issue](https://github.com/CityOfZion/neo-python/issues/new) if you encounter a problem.
- Or ping **@localhuman**  or **@metachris** on the [NEO Discord](https://discord.gg/R8v48YA).
- Pull requests welcome. You can help with wallet functionality, writing tests or documentation, or on any other feature you deem awesome. All successful pull requests will be rewarded with one photo of a cat or kitten.


## Getting started

You will need to install the libleveldb library. Install [Python 3.5](https://www.python.org/downloads/release/python-354/) to make sure you don't run into any issues with your version of Python being different than the current maintainer's version. Note that Python 3.6 is not currently supported due to incompatibilities with the byteplay module.

We have published a Youtube [video](https://youtu.be/oy6Z_zd42-4) to help get you started with this library. There are other videos under the [CityOfZion](https://www.youtube.com/channel/UCzlQUNLrRa8qJkz40G91iJg) Youtube channel.

##### OSX:

```
brew install leveldb
```

##### Ubuntu/Debian

```
apt-get install libleveldb-dev python3.5-dev python3-pip python3-venv libssl-dev g++
```

##### Centos/Redhat/Fedora

This is a bit more tricky...

```
# Install Python 3.5:
yum install -y centos-release-scl
yum install -y rh-python35
scl enable rh-python35 bash

# Install dependencies:
yum install -y epel-release
yum install -y readline-devel leveldb-devel libffi-devel gcc-c++ redhat-rpm-config gcc python-devel openssl-devel
```

### For all of these, make sure that the `Chains` directory in your project has the proper write permissions

##### Windows

Not sure. Installing the Python package plyvel seems to require C++ compiler support tied to Visual Studio and libraries.

-------------------

### Virtual Environment

Now navigate into the project, make a Python 3 virtual environment and activate
it via

```
python3.5 -m venv venv
source venv/bin/activate
```

Then install the requirements:

```
pip install -U setuptools pip wheel
pip install -e .
```

## Running
After installing requirements and activating your environment, there is an easy
to use `prompt.py` file for you to run the node as well as some basic interactivity

```
python prompt.py
NEO cli. Type 'help' to get started

neo> state
Progress: 1054913 / 1237188

neo>
```

You can query for a block in the current server by hash or by block index:

```
python prompt.py
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
```


#### Available Wallet commands

```
help

create wallet {wallet_path}
open wallet {wallet_path}

wallet { verbose } { rebuild } {rebuild BLOCK_HEIGHT}
export wif { ADDRESS }
import wif { WIF }

send { ASSET_ID } { ADDRESS } { AMOUNT }
```


#### Extra notes

To run the prompt on mainnet, you can use the cli argument `-m`:

```
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
```

On OSX, if you would like to run the process in the background, even when your computer is sleeping, you can use the built in `caffeinate` command

```
caffeinate python prompt.py
```

### Logging

Currently, `prompt.py` logs to `prompt.log`

## Tests

Tests are important. Currently there are not enough, but we are working on that. You can start them by running this commands:

    make test
    make coverage

Note that some of the unit tests use a giant blockchain fixture database ( around 800mb ). This file is not kept in the repo.

When running tests the first time, the test setup will try to download the file and extract it to the proper directory.
**Long story short**: the first time you run your tests, it will take a while to download those fixtures. After that it should be pretty quick.


## Useful commands

    make lint
    make test
    make coverage
    make docs


## Updating the version number and releasing new versions of neo-python

(Only for admins)

This is a checklist for releasing a new version:

.. code-block:: console

    # In case you want to increase the version number again (eg. scope changed from patch to minor):
    bumpversion --no-tag patch|minor|major

    # Update ``CHANGELOG.md`` and ``docs/source/changelog.rst`` with the new version number and the changes and commit this
    vi CHANGELOG.md docs/source/changelog.rst
    git commit -m "Updated Changelogs" CHANGELOG.md docs/source/changelog.rst

    # Set the release version number and create the tag
    bumpversion release

    # Increase patch number and add `-dev`
    bumpversion --no-tag patch

    # Push to GitHub, which also updates the PyPI package
    git push && git push --tags

## Troubleshooting

If you encounter any problems, please take a look at the [installation section](https://neo-python.readthedocs.io/en/latest/install.html#further-install-notes) in the docs, and if that doesn't help open an issue. We'll try to help.


## License

- Open-source [MIT](https://github.com/CityOfZion/neo-python/blob/master/LICENSE.md).
- Main author is [@localhuman](https://github.com/localhuman).


## Donations

Accepted at __ATEMNPSjRVvsXmaJW4ZYJBSVuJ6uR2mjQU__
