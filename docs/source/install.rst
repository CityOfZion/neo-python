
Installation
------------

You will need to install the libleveldb library. Install `Python 3.5 <https://www.python.org/downloads/release/python-354/>`_ to make sure you don't run into any issues with your version of Python being different than the current maintainer's version. Note that Python 3.6 is not currently supported due to incompatibilities with the byteplay module.

Installation via ``pip`` is not currently available at this time

You should install platform specific items before installing from git.



Install from Git
================

Clone the repository at `https://github.com/CityOfZion/neo-python/ <https://github.com/CityOfZion/neo-python/>`_ and navigate into the project directory.
Make a Python 3 virtual environment and activate it via

::

    python3 -m venv venv
    source venv/bin/activate

or to explicitly install Python 3.5,

::

    virtualenv -p /usr/local/bin/python3.5 venv
    source venv/bin/activate

Then install the requirements via

::

    pip install -r requirements.txt

If you plan on doing development, install ``requirements_dev.txt`` instead




Platform Specific Instructions
==============================

OSX
^^^

::

    brew install leveldb

Ubuntu/Debian
^^^^^^^^^^^^^

::

    apt-get install libleveldb-dev python3.5-dev python3-pip libssl-dev

Centos/Redhat/Fedora
^^^^^^^^^^^^^^^^^^^^

This is a bit more tricky. You may need to enable the epel repo for the leveldb-devel package, which you can do by editing ``/etc/yum.repos.d/epel.repo``.

::

    yum -y install development tools python35 python35-devel python35-pip readline-devel leveldb-devel libffi-devel


Windows
^^^^^^^
This has not been tested at this time. Installing the Python package plyvel seems to require C++ compiler support tied to Visual Studio and libraries.


Further Install Notes
=====================

For all of these, make sure that the ``Chains`` directory in your project has the proper write permissions


Common issues on OSX
^^^^^^^^^^^^^^^^^^^^

If you're having an issue similar to this:

.. code-block:: sh

    from ._plyvel import (  # noqa
    ImportError: dlopen(neo-python/venv/lib/python3.5/site-packages/plyvel/_plyvel.cpython-35m-darwin.so, 2): Symbol not found: __ZN7leveldb2DB4OpenERKNS_7Options
    ERKSsPPS0_
    Referenced from: neo-python/venv/lib/python3.5/site-packages/plyvel/_plyvel.cpython-35m-darwin.so
    Expected in: flat namespace


You may need to uninstall plyvel (python libleveldb library), and reinstall with the following cflags

.. code-block:: sh

    pip uninstall plyvel
    CFLAGS='-mmacosx-version-min=10.7 -stdlib=libc++' pip install --no-use-wheel plyvel --no-cache-dir --global-option=build_ext --global-option="-I/usr/local/Cellar/leveldb/1.20_2/include/" --global-option="-L/usr/local/lib"


You may also encounter issues when installing the pycrypto module on OSX:

.. code-block:: sh

    src/_fastmath.c:36:11: fatal error: 'gmp.h' file not found
    # include <gmp.h>
              ^~~~~~~
    330 warnings and 1 error generated.
    error: command 'clang' failed with exit status 1

This may be fixed by installing the gmp library using homebrew and running pip install with the following commandline:

.. code-block:: sh

    brew install gmp
    CFLAGS='-mmacosx-version-min=10.7 -stdlib=libc++' pip install --no-use-wheel pycrypto --no-cache-dir --global-option=build_ext --global-option="-I/usr/local/Cellar/gmp/6.1.2/include/" --global-option="-L/usr/local/lib"
