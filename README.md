# neo-python: Python SDK for NEO platform

In progress, please reach out in order to contribute

## Getting started


you will need to install the libleveldb library. 

##### on OSX:
```
brew install leveldb
```

##### ubuntu/debian
```
apt-get -s install libleveldb-dev
```

##### centos/redhat/fedora is a bit more tricky...
```
yum -y install development tools python35 python35-devel python35-pip readline-devel leveldb-devel libffi-devel
```

you may need to enable the epel repo for the leveldb-devel package, which you can do by editing `/etc/yum.repos.d/epel.repo`

### For all of these, make sure that the `Chains` directory in your project has the proper write permisisons

##### windows ( not sure )


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

After installing requirements and activating your environment, there is an easy to use `prompt.py` file for you to run the node as well as some basic interactivity

```
python prompt.py 
NEO cli. Type 'help' to get started

neo> show state
Progress: 1054913 / 1237188

neo> 
```

You can query for a block in the current server by hash or by block index:

```
python prompt.py 
NEO cli. Type 'help' to get started

neo> show block 122235
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


If you dont want interactivity, but just want to run the server you can simply run the `node.py` file:

```
python node.py 
```


### Logging

Currently, `prompt.py` logs to `prompt.log`, while the `node.py` does not log.



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
