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

### What will it do

- Full Python RPC client
- Compile smart contracts written in Python and deploy them to the blockchain
- Full smart contract debugging and inspection

### Get Help or give help

- Open a new [issue](https://github.com/CityOfZion/neo-python/issues/new) if you encounter a problem.
- Or ping **@localhuman** on the [NEO Slack](https://join.slack.com/t/neoblockchainteam/shared_invite/MjE3ODMxNDUzMDE1LTE1MDA4OTY3NDQtNTMwM2MyMTc2NA).
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
apt-get install libleveldb-dev python3.5-dev python3-pip libssl-dev
```

##### Centos/Redhat/Fedora

This is a bit more tricky...

```
yum -y install development tools python35 python35-devel python35-pip readline-devel leveldb-devel libffi-devel
```

You may need to enable the epel repo for the leveldb-devel package, which you can do by editing `/etc/yum.repos.d/epel.repo`.

### For all of these, make sure that the `Chains` directory in your project has the proper write permissions

##### Windows

Not sure. Installing the Python package plyvel seems to require C++ compiler support tied to Visual Studio and libraries.

-------------------

### Virtual Environment

Now navigate into the project, make a Python 3 virtual environment and activate
it via

```
python3 -m venv venv
source venv/bin/activate
```

or to install Python 3.5 specifically

```
virtualenv -p /usr/local/bin/python3.5 venv
source venv/bin/activate
```

Then install requirements
```
pip install -r requirements.txt
```

Finally, install a reference to the `neo` working directory, which allows to `import neo` from
anywhere in the project (eg. examples):
```
pip install -e .
```


### Installing on OSX

If you're having an issue similar to this:

```
    from ._plyvel import (  # noqa
    ImportError: dlopen(neo-python/venv/lib/python3.5/site-packages/plyvel/_plyvel.cpython-35m-darwin.so, 2): Symbol not found: __ZN7leveldb2DB4OpenERKNS_7Options
    ERKSsPPS0_
    Referenced from: neo-python/venv/lib/python3.5/site-packages/plyvel/_plyvel.cpython-35m-darwin.so
    Expected in: flat namespace
```

You may need to uninstall plyvel (python libleveldb library), and reinstall with the following cflags

```
pip uninstall plyvel
CFLAGS='-mmacosx-version-min=10.7 -stdlib=libc++' pip install --no-use-wheel plyvel --no-cache-dir --global-option=build_ext --global-option="-I/usr/local/Cellar/leveldb/1.20_2/include/" --global-option="-L/usr/local/lib"
```

You may also encounter issues when installing the pycrypto module on OSX:

```
src/_fastmath.c:36:11: fatal error: 'gmp.h' file not found
# include <gmp.h>
          ^~~~~~~
330 warnings and 1 error generated.
error: command 'clang' failed with exit status 1
```

This may be fixed by installing the gmp library using homebrew and running pip install with the following commandline:

```
brew install gmp
CFLAGS='-mmacosx-version-min=10.7 -stdlib=libc++' pip install --no-use-wheel pycrypto --no-cache-dir --global-option=build_ext --global-option="-I/usr/local/Cellar/gmp/6.1.2/include/" --global-option="-L/usr/local/lib"
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
usage: prompt.py [-h] [-m] [-c CONFIG]

optional arguments:
  -h, --help            show this help message and exit
  -m, --mainnet         use MainNet instead of the default TestNet
  -c CONFIG, --config CONFIG
                        Use a specific config file
```

On OSX, if you would like to run the process in the background, even when your computer is sleeping, you can use the built in `caffeinate` command

```
caffeinate python prompt.py
```

### Logging

Currently, `prompt.py` logs to `prompt.log`

## Tests

Tests are important. Currently there are not enough, but we are working on that. You can start them by running this command.

Note that some of the unit tests use a giant blockchain fixture database ( around 800mb ). This file is not kept in the repo.

When running tests the first time, the test setup will try to download the file and extract it to the proper directory.

**Long story short**: the first time you run your tests, it will take a while to download those fixtures. After that it should be pretty quick.

```
python -m unittest discover neo
```

To run tests with `coverage`, use the following

```
coverage run -m unittest discover neo
```

After that, you can generate a command line coverage report use the following:

```
coverage report -m --omit=venv/*
```

## License

- Open-source [MIT](https://github.com/CityOfZion/neo-python/blob/master/LICENSE.md).
- Main author is [@localhuman](https://github.com/localhuman).


## Donations

Accepted at __ATEMNPSjRVvsXmaJW4ZYJBSVuJ6uR2mjQU__
