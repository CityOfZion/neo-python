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
  <a href='https://coveralls.io/github/CityOfZion/neo-python?branch=master'>
    <img src='https://coveralls.io/repos/github/CityOfZion/neo-python/badge.svg?branch=master' alt='Coverage Status' />
  </a>
</p>

## Overview

### What does it currently do

- This project aims to be a full port of the [C# code](https://github.com/neo-project/neo) at [Neo Project](https://github.com/neo-project) 
- Run a python based P2P node
- Interactive CLI for configuring node and inspecting block chain
- Runs smart contracts on the block chain in a python virtual machine
- Very basic Wallet functionality (Not fully tested, please do not use on mainnet)

### What will it do

- Full python RPC client
- Compile smart contracts written python and deploy to blockchain
- Full smart contract debugging and inspection

### Get Help or give help

- Open a new [issue](https://github.com/CityOfZion/neo-python/issues/new) if you encounter a problem.
- Or ping [@localhuman](https://github.com/localhuman) on the [NEO Slack](https://join.slack.com/t/neoblockchainteam/shared_invite/MjE3ODMxNDUzMDE1LTE1MDA4OTY3NDQtNTMwM2MyMTc2NA).
- Pull requests are welcome. You can help with wallet functionality, writing tests or documentation, or on any other feature you deem awesome.  All successful pull requests will be rewarded with one photo of a cat or kitten. 

### License

- Open-source [Apache 2.0](https://github.com/CityOfZion/neo-python/blob/master/LICENSE).
- Main author is [@localhuman](https://github.com/localhuman).

### Project structure

```
neo-python
├── compiler.py
├── prompt.py            <─── terminal client
├── node.py
└── neo
    ├── Core
        ├── State
        └── TX
    ├── Cryptography
    ├── Implementations
        ├── Blockchains
            ├── LevelDB
            └── RPC
        └── Wallets
    ├── IO
    ├── Network
        └── Payloads
    ├── SmartContract
        ├── Framework
            ├── Neo
            └── System
    ├── Utils
    ├── VM
    └── Wallets
```

## Getting started

Here are some pointers to install the package and exectute the terminal client pointed out in the tree above.

### Dependencies

You will need to install the lib[leveldb](https://en.wikipedia.org/wiki/LevelDB) library, 
use for many blockchain projects:

##### On OSX:
```
brew install leveldb
```

##### On ubuntu/debian
```
apt-get -s install libleveldb-dev
```

##### Centos/Redhat/Fedora 
This is a bit more tricky...
```
yum -y install development tools python35 python35-devel python35-pip readline-devel leveldb-devel libffi-devel
```

You may need to enable the epel repo for the leveldb-devel package, which you can do by editing 
`/etc/yum.repos.d/epel.repo`

For all of these, make sure that the `Chains` directory in your project has the proper write permisisons

##### Windows
Not sure. Installing the Python package plyvel seems to require C++ compiler support tied to Visual Studio and libraries.

-------------------

Now navigate into the project, make a Python 3 virtual environment and activate it via
```
python3 -m venv venv
source venv/bin/activate
```

Then install requirements
```
pip install -r requirements.txt
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
CFLAGS='-mmacosx-version-min=10.7 -stdlib=libc++' pip install --no-use-wheel plyvel --no-cache-dir
```

Moreover, this pip installation must see the leveldb header file db.h.
You may need to add flags similar to the following to the
installation command

```
--global-option=build_ext
--global-option="-I/usr/local/Cellar/leveldb/1.20_2/include/"
--global-option="-L/usr/local/lib"
```

## Running

After installing requirements and activating your environment, 
there is an easy to use `prompt.py` file for you to run the node 
as well as some basic interactivity:

![opening prompt.py](http://i.imgur.com/jQklFSB.png)

You can query for a block in the current server by hash or by block index:

![inspecting block](http://i.imgur.com/njTiHL3.png)

#### Available Wallet commands

```
create wallet {wallet_path}
open wallet {wallet_path}

wallet { verbose } { rebuild } {rebuild BLOCK_HEIGHT}
export wif { ADDRESS }
import wif { WIF }

send { ASSET_ID } { ADDRESS } { AMOUNT }

```

#### Logging

Currently, `prompt.py` logs to `prompt.log`


#### Misc
On OSX, if you would like to run the process in the background, even when your computer is sleeping, you can use the built in `caffeinate` command
```
caffeinate python prompt.py
```

## Module testing

Tests are important.  Currently there are not enough, but we are working on that.  You can start them by running this command

Note that some of the unit tests use a giant blockchain fixture database (around 800mb).  This file is not kept in the repo.

When running tests the first time, the test setup will try to download the file and extract it to the proper directory

Long story short, the first time you run your tests, it will take a while to download those fixtures. After that it should be pretty quick.

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
