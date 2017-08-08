# neo-python: Python SDK for NEO platform

In progress, please reach out in order to contribute

## Getting started


you will need to install the libleveldb library. on OSX:
```
brew install leveldb
```

ubuntu/debian
```
apt-get -s install libleveldb-dev
```

centos/redhat/fedora
```
yum -y install libleveldb-dev
```

windows ( not sure )


-------------------

make a python 3 virtual environment, and activate it
```
python3 -m venv venv
source venv/bin/activate
```

then install requirements
```
pip install -r requirements.txt
```


### Installing on OSX

if you're having an issue similar to this:

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

## Running

After installing requirements and activating your environment, there is an easy to use `cli.py` file for you to run the node as well as some basic interactivity

```
python cli.py 
> Starting Server... Please wait
> Neo console. Type 'help' for help.
> show state
> Progress: 230003 / 1210000      Ok.. what next?
```

You can query for a block in the current server by hash or by block index:

```
python cli.py 
> Starting Server... Please wait
> Neo console. Type 'help' for help.
> show
> what should i show?  try 'block ID/hash', 'header ID/hash 'tx hash', 'state', or 'nodes' 

show block 11335
{
  "hash": "39684763ea1f6e27f27813017b9a75041ea51a0fc9856bef42e839c4efe268df",
  "merkleroot": "337afb56abfcc81228d0f12fafffdcc74c4c820c1cca68e0f37c4b46b052218d",
  "previousblockhash": "7ef806ab2b4e8719c87c78242c83ff839f5cca28d1b55b526cca6879b8347f23",
  "consensus data": 1643989216319287762,
  "index": 11335,
  "next_consensus": "59e75d652b5d3827bf04c165bbe9ef95cca4bf55",
  "script": "",
  "tx": [
    "337afb56abfcc81228d0f12fafffdcc74c4c820c1cca68e0f37c4b46b052218d"
  ],
  "time": 1476859946,
  "version": 0
}
Ok... what next?

>
```


If you dont want interactivity, but just want to run the server you can simply run the `node.py` file:

```
python node.py 
```


### Logging

Currently, `cli.py` logs to `cli.log`, while the `node.py` file logs to `nodes.log`



## Tests

Tests are important.  Currently there are not enough, but we are working on that.  You can start them by running this command

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
